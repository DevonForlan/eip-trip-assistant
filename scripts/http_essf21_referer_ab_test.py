"""Referer A/B test for ESSF21.aspx - GET-only, independent POC.

Question this isolates: in docs/http-webforms-poc.md, requests+SSPI got
an empty (Content-Length 0) body from ESSF21.aspx, while the real
browser capture (docs/browser-vs-http-sequence.md) got a full 144,494-byte
response and DID send a Referer header pointing at the EPIE001.aspx
wrapper. This script tests whether that Referer header is what actually
makes the difference, using 6 fully independent sessions (3 without
Referer, 3 with) so a single lucky/unlucky run can't decide the answer.

Deliberately isolated from src/ (self-contained: stdlib + requests +
requests_negotiate_sspi only) and issues GET requests exclusively -
grep this file for ".post(" before trusting that claim, don't just take
the docstring's word for it.

Each of the 6 runs is a brand-new requests.Session() that does its own
fresh EFNET -> EPIE001 -> ESSF21 walk, so no two runs ever share the
same Identifier (the whole point is to stop conflating "maybe the
Identifier from run N was already consumed" with "Referer matters").

Masking rules (same philosophy as scripts/http_eip_explorer.py and
scripts/capture_browser_sequence.py):
- Cookie names only, never values.
- Identifier (and LoginId/ClientIP, same as before): never the raw
  value - only length + sha256 first 8 hex chars.
- Authorization: never read or printed anywhere in this file.
- Raw ESSF21 response bodies are saved under logs/http_essf21_ab_test/
  (already gitignored via the existing "logs/" entry) purely so a human
  can inspect a successful one later - never printed to console or
  embedded in the generated doc.

Run:
    python scripts/http_essf21_referer_ab_test.py
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlparse

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import requests
    from dotenv import load_dotenv
    from requests_negotiate_sspi import HttpNegotiateAuth
except ImportError as e:  # noqa: BLE001
    print(f"[error] Missing dependency - run: pip install -r requirements.txt ({e})")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "logs" / "http_essf21_ab_test"

load_dotenv(ROOT / ".env")

EIP_HOST = os.environ.get("EIP_URL", "http://eip.example.com/EFNET/") \
    .split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]
EIP_URL = f"http://{EIP_HOST}/EFNET/"
EPIE001_URL = f"http://{EIP_HOST}/EFNET/src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21"

TIMEOUT_SECONDS = 15
SENSITIVE_QUERY_PARAMS = {"identifier", "loginid", "clientip"}
TARGET_MARKERS = ["ESSCCDJ024_txt", "ESSCCDJ028_txt", "__VIEWSTATE", "__EVENTVALIDATION"]

# A run counts as a real success only with a substantial body - the
# known-good size is ~144KB, the known-empty-failure size is exactly 0.
# 10,000 is a deliberately conservative middle point, nowhere near either
# observed value, so no real result should ever land ambiguously near it.
SUCCESS_BODY_LEN_THRESHOLD = 10_000


def _hash_summary(value) -> dict:
    if not value:
        return {"present": False, "length": 0, "sha256_prefix8": ""}
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:8]
    return {"present": True, "length": len(value), "sha256_prefix8": digest}


def _get_query_param(url: str, name: str):
    parsed = urlparse(url)
    for k, v in parse_qsl(parsed.query, keep_blank_values=True):
        if k.lower() == name.lower():
            return v
    return None


def _mask_url(url: str) -> str:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    if not pairs:
        return base
    parts = []
    for k, v in pairs:
        if k.lower() in SENSITIVE_QUERY_PARAMS:
            s = _hash_summary(v)
            parts.append(f"{k}=<len{s['length']},sha256[:8]={s['sha256_prefix8']}>")
        else:
            parts.append(f"{k}={v}")
    return base + "?" + "&".join(parts)


def _extract_essf21_src(html_text: str, base_url: str):
    m = re.search(r'<i?frame[^>]+src="([^"]*ESSF21\.aspx[^"]*)"', html_text, re.IGNORECASE)
    if not m:
        return None
    return urljoin(base_url, m.group(1))


def _cookie_names(session) -> list:
    return sorted({c.name for c in session.cookies})


def _has_cookie(session, name: str) -> bool:
    return any(c.name == name for c in session.cookies)


def _save_text(name: str, text: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(text, encoding="utf-8", errors="replace")


def run_single(label: str, use_referer: bool, run_index: int) -> dict:
    tag = f"{label}{run_index}"
    print(f"\n--- Run {tag} (Referer: {'yes' if use_referer else 'no'}) ---")

    result = {
        "run_label": label,
        "run_index": run_index,
        "tag": tag,
        "use_referer": use_referer,
    }

    session = requests.Session()
    session.auth = HttpNegotiateAuth()

    try:
        r_efnet = session.get(EIP_URL, timeout=TIMEOUT_SECONDS)
        result["efnet_status"] = r_efnet.status_code
    except requests.RequestException as e:
        result["error"] = f"GET of EFNET failed: {e}"
        print(f"  [error] {result['error']}")
        return result

    try:
        t_epie001_end_deadline = time.monotonic()
        r_epie001 = session.get(EPIE001_URL, timeout=TIMEOUT_SECONDS)
        t_epie001_end = time.monotonic()
    except requests.RequestException as e:
        result["error"] = f"GET of EPIE001 failed: {e}"
        print(f"  [error] {result['error']}")
        return result

    r_epie001.encoding = "utf-8"
    result["epie001_status"] = r_epie001.status_code
    result["epie001_content_length"] = len(r_epie001.content)

    essf21_url = _extract_essf21_src(r_epie001.text, r_epie001.url)
    if essf21_url is None:
        result["essf21_url_found"] = False
        result["outcome"] = "EPIE001_NO_FRAME"
        print("  [warn] This EPIE001 response has no ESSF21 <frame> tag (the same slim "
              "response documented in http-webforms-poc.md), so there is no URL to "
              "test Referer against. Skipping this run.")
        return result

    result["essf21_url_found"] = True
    identifier_value = _get_query_param(essf21_url, "Identifier")
    result["identifier"] = _hash_summary(identifier_value)
    result["epie001_url_masked"] = _mask_url(r_epie001.url)

    headers = {}
    if use_referer:
        headers["Referer"] = r_epie001.url

    t_essf21_start = time.monotonic()
    try:
        r_essf21 = session.get(essf21_url, timeout=TIMEOUT_SECONDS, headers=headers, allow_redirects=True)
    except requests.RequestException as e:
        result["error"] = f"GET of ESSF21 failed: {e}"
        print(f"  [error] {result['error']}")
        return result

    delay_ms = (t_essf21_start - t_epie001_end) * 1000
    body = r_essf21.content
    text_for_search = body.decode("utf-8", errors="replace")

    result.update(
        {
            "essf21_status": r_essf21.status_code,
            "essf21_final_url_masked": _mask_url(r_essf21.url),
            "essf21_content_type": r_essf21.headers.get("Content-Type", ""),
            "essf21_content_length_header": r_essf21.headers.get("Content-Length", ""),
            "essf21_body_len": len(body),
            "has_aspnet_sessionid_cookie": _has_cookie(session, "ASP.NET_SessionId"),
            "cookie_names": _cookie_names(session),
            "markers": {m: (m in text_for_search) for m in TARGET_MARKERS},
            "delay_epie001_to_essf21_ms": round(delay_ms, 1),
        }
    )
    result["outcome"] = (
        "SUCCESS" if len(body) >= SUCCESS_BODY_LEN_THRESHOLD
        else "EMPTY_200" if r_essf21.status_code == 200
        else "OTHER"
    )

    if len(body) > 0:
        _save_text(f"run_{tag}_essf21.html", text_for_search)

    print(f"  EPIE001: status={result['epie001_status']} len={result['epie001_content_length']}")
    print(f"  ESSF21 : status={result['essf21_status']} body_len={result['essf21_body_len']} "
          f"outcome={result['outcome']} delay={result['delay_epie001_to_essf21_ms']}ms")
    print(f"  markers: {result['markers']}")

    return result


def _classify(results: list) -> tuple:
    a_runs = [r for r in results if r["run_label"] == "A" and "outcome" in r and r["outcome"] != "EPIE001_NO_FRAME"]
    b_runs = [r for r in results if r["run_label"] == "B" and "outcome" in r and r["outcome"] != "EPIE001_NO_FRAME"]

    a_success = sum(1 for r in a_runs if r["outcome"] == "SUCCESS")
    a_empty = sum(1 for r in a_runs if r["outcome"] == "EMPTY_200")
    b_success = sum(1 for r in b_runs if r["outcome"] == "SUCCESS")
    b_empty = sum(1 for r in b_runs if r["outcome"] == "EMPTY_200")

    counts = {
        "a_total_testable": len(a_runs),
        "a_success": a_success,
        "a_empty": a_empty,
        "b_total_testable": len(b_runs),
        "b_success": b_success,
        "b_empty": b_empty,
        "a_no_frame": sum(1 for r in results if r["run_label"] == "A" and r.get("outcome") == "EPIE001_NO_FRAME"),
        "b_no_frame": sum(1 for r in results if r["run_label"] == "B" and r.get("outcome") == "EPIE001_NO_FRAME"),
    }

    if len(a_runs) < 2 or len(b_runs) < 2:
        return "INCONCLUSIVE", counts, (
            "Fewer than 2 runs in group A or B actually got as far as testing Referer "
            "(EPIE001 too often returned no ESSF21 URL). Not enough data to conclude."
        )

    if a_empty >= 2 and a_success == 0 and b_success >= 2 and b_empty == 0:
        return "REFERER_LIKELY_NECESSARY", counts, (
            "A (no Referer) consistently returned an empty body while B (with Referer) "
            "consistently succeeded - strong evidence that Referer is required."
        )

    if a_success >= 2 and b_success >= 2:
        return "REFERER_NOT_NECESSARY", counts, (
            "Both A and B succeeded, so the earlier requests-based failures are more "
            "likely about a stale Identifier, session state or timing. Referer is ruled out."
        )

    if a_success == 0 and b_success == 0:
        return "BOTH_FAILED", counts, (
            "Neither A nor B ever succeeded, so Referer is not the (only) factor. "
            "The next step is a header-by-header comparison - not attempted here."
        )

    return "INCONCLUSIVE", counts, (
        "Results are inconsistent (groups disagree internally, or land somewhere in "
        "between), so no clear conclusion can be drawn."
    )


def main():
    print(f"EIP_HOST = {EIP_HOST}")
    print(f"Output directory (gitignored) = {OUT_DIR}")
    print("Running 6 fully independent sessions: A1, B1, A2, B2, A3, B3 - interleaved, "
          "so a drift over time cannot masquerade as a group difference.\n")

    results = []
    for i in range(1, 4):
        results.append(run_single("A", use_referer=False, run_index=i))
        results.append(run_single("B", use_referer=True, run_index=i))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    verdict, counts, explanation = _classify(results)

    print("\n=== Summary ===")
    print(json.dumps(counts, ensure_ascii=False, indent=2))
    print(f"\nVerdict: {verdict}")
    print(f"Reason : {explanation}")

    (OUT_DIR / "verdict.json").write_text(
        json.dumps({"verdict": verdict, "counts": counts, "explanation": explanation}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nFull results written to {OUT_DIR / 'results.json'}; "
          f"verdict to {OUT_DIR / 'verdict.json'}.")


if __name__ == "__main__":
    main()
