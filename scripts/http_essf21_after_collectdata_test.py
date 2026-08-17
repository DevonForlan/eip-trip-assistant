"""Can pure HTTP reach the real ESSF21 form once CollectData.aspx has run?
GET-only, independent POC.

Established in docs/http-epie001-init-condition.md: GETting
CollectData.aspx in the same session is the necessary initialization step
that makes EPIE001.aspx return the full ~91.7KB version (5/5 reproducible)
instead of the 15,275-byte slim one. That answered the EPIE001 question
but deliberately stopped short of fetching ESSF21.

This script closes that remaining gap: with CollectData in the sequence,
does the ESSF21 GET still come back as the 200-with-empty-body seen in
docs/http-webforms-poc.md, or does it return the real ~140KB form the
browser gets (docs/browser-vs-http-sequence.md recorded 144,494 bytes)?

Answer, found by leave-one-out header search after this script's first
run came back 200 + 0 bytes 3/3: ESSF21 additionally requires an
**Accept-Language** request header. Without it the ASP.NET 2.0 HRMESS
page writes nothing at all (200, Content-Length: 0, and no Content-Type
header whatsoever) - consistent with the I18NLanguageType field this
form carries. Accept-Language alone is both necessary and sufficient;
Referer and Accept turned out irrelevant here, and cookie scoping was
ruled out (the session cookie is path=/ and does reach /HRMESS/).

User-Agent is not required but does change what gets rendered: with a
browser UA the response is ~144,500 bytes and includes __EVENTTARGET;
without one it is ~136,980 bytes and __EVENTTARGET is absent. Since
__EVENTTARGET is what any future postback would need, this script sends
a browser UA too.

Fixed sequence per run, all in ONE fresh session:
    GET /EFNET/
    GET <the CollectData.aspx URL parsed out of /EFNET/'s own frame src>
    GET EPIE001.aspx?FormID=ESSF21          (Referer: none needed - ruled out)
    GET <the ESSF21 URL parsed out of THAT EPIE001 response>
                                            (Referer: that EPIE001 URL,
                                             kept for browser fidelity even
                                             though it proved unnecessary)

Nothing is hardcoded that can go stale: the CollectData URL is resolved
from /EFNET/'s frame src rather than assumed, and the ESSF21 URL (and its
Identifier) is parsed fresh from each run's own EPIE001 response. No URL
or Identifier is ever reused across runs.

Scope limits:
  - GET only. Grep for ".post(" to verify rather than trusting this.
  - Reads the form; never fills, saves, sends, or calls btClosejQTab.
  - Touches nothing in src/ - the working Playwright flow is untouched.

Masking: cookie NAMES only (never values); Identifier/LoginId/ClientIP
reduced to length + sha256[:8]; Authorization never read; response bodies
hashed and written to logs/http_essf21_after_collectdata/ (gitignored)
for offline human inspection rather than printed.

Run:
    python scripts/http_essf21_after_collectdata_test.py
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
OUT_DIR = ROOT / "logs" / "http_essf21_after_collectdata"

load_dotenv(ROOT / ".env")

HOST = os.environ.get("EIP_URL", "http://eip.example.com/EFNET/") \
    .split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]
EFNET = f"http://{HOST}/EFNET/"
EPIE001 = f"http://{HOST}/EFNET/src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21"

# 60s, not 20s: the full-version EPIE001 path was observed to block
# transiently (3,687ms, then >20s three times, then 0.4s). A short ceiling
# conflates "transiently blocked" with "server answered with the slim
# version" - see docs/http-epie001-init-condition.md.
TIMEOUT_SECONDS = 60
RUNS = 3

SESSION_COOKIE = "ASP.NET_SessionId"
SENSITIVE_QUERY_PARAMS = {"identifier", "loginid", "clientip"}

# Accept-Language is the one header ESSF21 genuinely requires (see module
# docstring); the UA is here for render completeness, not access. Set on
# the session because a real browser sends both on every request.
BROWSER_HEADERS = {
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ),
}

EPIE001_FULL_MIN_BYTES = 50_000
# Browser got 144,494 bytes; the known failure mode is exactly 0. 50,000
# sits nowhere near either, so no real result lands ambiguously on it.
ESSF21_SUCCESS_MIN_BYTES = 50_000

ESSF21_MARKERS = [
    "ESSCCDJ024_txt",
    "ESSCCDJ028_txt",
    "ESSCCDJ037_txt",
    "ESSCCDD005_txt",
    "__VIEWSTATE",
    "__EVENTVALIDATION",
    "__EVENTTARGET",
]


def _hash_summary(value) -> dict:
    if not value:
        return {"present": False, "length": 0, "sha256_prefix8": ""}
    return {
        "present": True,
        "length": len(value),
        "sha256_prefix8": hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:8],
    }


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
    return f"{base}?{'&'.join(parts)}"


def _cookie_names(session) -> list:
    return sorted({c.name for c in session.cookies})


def _first_frame_src_matching(html_text: str, base_url: str, needle: str):
    """Resolve a frame/iframe src containing `needle` against base_url -
    used so neither the CollectData nor the ESSF21 URL is hardcoded."""
    m = re.search(
        r'<i?frame[^>]+src="([^"]*' + re.escape(needle) + r'[^"]*)"',
        html_text,
        re.IGNORECASE,
    )
    if not m:
        return None
    return urljoin(base_url, m.group(1))


def _get_query_param(url: str, name: str):
    for k, v in parse_qsl(urlparse(url).query, keep_blank_values=True):
        if k.lower() == name.lower():
            return v
    return None


def run_once(run_index: int) -> dict:
    print(f"\n{'=' * 72}\nRun {run_index}/{RUNS} (fresh session)\n{'=' * 72}")
    r = {"run_index": run_index}

    session = requests.Session()
    session.auth = HttpNegotiateAuth()
    session.headers.update(BROWSER_HEADERS)
    r["headers_sent"] = sorted(BROWSER_HEADERS.keys())

    # --- Step 1: /EFNET/ ---
    try:
        resp_efnet = session.get(EFNET, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as e:
        r["outcome"] = "EFNET_FAILED"
        r["error"] = str(e)
        print(f"  [error] GET /EFNET/ -> {e}")
        return r
    resp_efnet.encoding = "utf-8"
    r["efnet"] = {"status": resp_efnet.status_code, "bytes": len(resp_efnet.content)}
    print(f"  GET /EFNET/                       {resp_efnet.status_code} {len(resp_efnet.content):>9,}B")

    # --- Step 2: CollectData.aspx, resolved from the homepage itself ---
    collect_url = _first_frame_src_matching(resp_efnet.text, resp_efnet.url, "CollectData.aspx")
    if collect_url is None:
        r["outcome"] = "COLLECTDATA_URL_NOT_FOUND"
        print("  [error] No frame src pointing at CollectData.aspx in the homepage HTML "
              "- the homepage structure may have changed.")
        return r
    r["collectdata_url"] = _mask_url(collect_url)

    try:
        resp_collect = session.get(collect_url, timeout=TIMEOUT_SECONDS, allow_redirects=True)
    except requests.RequestException as e:
        r["outcome"] = "COLLECTDATA_FAILED"
        r["error"] = str(e)
        print(f"  [error] GET CollectData.aspx -> {e}")
        return r

    names_after_collect = _cookie_names(session)
    r["collectdata"] = {
        "status": resp_collect.status_code,
        "bytes": len(resp_collect.content),
        "final_url": _mask_url(resp_collect.url),
        "redirected": bool(resp_collect.history),
        "cookie_names": names_after_collect,
        "sessionid_present": SESSION_COOKIE in names_after_collect,
    }
    print(f"  GET CollectData.aspx              {resp_collect.status_code} {len(resp_collect.content):>9,}B "
          f"sid={'Y' if r['collectdata']['sessionid_present'] else 'N'} "
          f"redirect={'Y' if r['collectdata']['redirected'] else 'N'}")
    if not r["collectdata"]["sessionid_present"]:
        print(f"  [warn] Still no {SESSION_COOKIE} after this step, which contradicts "
              "earlier observations. Continuing, but treat the result with care.")

    # --- Step 3: EPIE001 (no Referer - already ruled out as necessary) ---
    try:
        resp_epie = session.get(EPIE001, timeout=TIMEOUT_SECONDS)
        t_epie_done = time.monotonic()
    except requests.RequestException as e:
        r["outcome"] = "EPIE001_FAILED"
        r["error"] = str(e)
        print(f"  [error] GET EPIE001 -> {e}")
        return r
    resp_epie.encoding = "utf-8"
    epie_bytes = len(resp_epie.content)
    r["epie001"] = {
        "status": resp_epie.status_code,
        "bytes": epie_bytes,
        "sha256_prefix12": hashlib.sha256(resp_epie.content).hexdigest()[:12],
        "is_full_version": epie_bytes >= EPIE001_FULL_MIN_BYTES,
    }
    print(f"  GET EPIE001.aspx?FormID=ESSF21    {resp_epie.status_code} {epie_bytes:>9,}B "
          f"{'full' if r['epie001']['is_full_version'] else 'slim'}")

    if not r["epie001"]["is_full_version"]:
        r["outcome"] = "EPIE001_SLIM"
        print("  [stop] No full EPIE001 this time, so there is no ESSF21 URL to parse. "
              "Ending this run.")
        return r

    # --- Step 4: ESSF21, URL parsed fresh from THIS run's EPIE001 ---
    essf21_url = _first_frame_src_matching(resp_epie.text, resp_epie.url, "ESSF21.aspx")
    if essf21_url is None:
        r["outcome"] = "ESSF21_URL_NOT_FOUND"
        print("  [error] A full EPIE001 with no ESSF21 frame src - that should not "
              "happen; inspect by hand.")
        return r

    identifier = _get_query_param(essf21_url, "Identifier")
    r["identifier"] = _hash_summary(identifier)
    r["essf21_url"] = _mask_url(essf21_url)

    t_essf21_start = time.monotonic()
    elapsed_ms = round((t_essf21_start - t_epie_done) * 1000, 1)
    r["elapsed_epie001_to_essf21_ms"] = elapsed_ms

    try:
        resp_essf21 = session.get(
            essf21_url,
            timeout=TIMEOUT_SECONDS,
            headers={"Referer": resp_epie.url},  # matches the real browser
            allow_redirects=True,
        )
    except requests.RequestException as e:
        r["outcome"] = "ESSF21_FAILED"
        r["error"] = str(e)
        print(f"  [error] GET ESSF21 -> {e}")
        return r

    body = resp_essf21.content
    text = body.decode("utf-8", errors="replace")
    names_final = _cookie_names(session)
    markers = {m: (m in text) for m in ESSF21_MARKERS}

    r["essf21"] = {
        "status": resp_essf21.status_code,
        "content_length_header": resp_essf21.headers.get("Content-Length", ""),
        "body_bytes": len(body),
        "content_type": resp_essf21.headers.get("Content-Type", ""),
        "redirected": bool(resp_essf21.history),
        "redirect_chain": [f"{h.status_code} {_mask_url(h.url)}" for h in resp_essf21.history],
        "final_url": _mask_url(resp_essf21.url),
        "sha256_prefix12": hashlib.sha256(body).hexdigest()[:12],
        "markers": markers,
        "cookie_names": names_final,
        "sessionid_present": SESSION_COOKIE in names_final,
        "referer_sent": "(this run's EPIE001 URL)",
    }

    if body:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"essf21_run{run_index}.html").write_text(text, encoding="utf-8", errors="replace")

    r["outcome"] = (
        "ESSF21_FULL" if len(body) >= ESSF21_SUCCESS_MIN_BYTES
        else "ESSF21_EMPTY_200" if resp_essf21.status_code == 200 and len(body) == 0
        else "ESSF21_OTHER"
    )

    print(f"  GET ESSF21.aspx                   {resp_essf21.status_code} {len(body):>9,}B "
          f"CL={r['essf21']['content_length_header'] or '(none)'} "
          f"ct={r['essf21']['content_type'] or '(none)'}")
    print(f"      redirect={'Y' if r['essf21']['redirected'] else 'N'}  "
          f"Identifier: len={r['identifier']['length']} sha256[:8]={r['identifier']['sha256_prefix8']}  "
          f"delay={elapsed_ms}ms")
    print(f"      markers: {markers}")
    print(f"      >>> {r['outcome']}")
    return r


def main():
    print("Fetching ESSF21 over plain HTTP, with CollectData.aspx initialization first")
    print(f"{RUNS} runs, each on a fresh session. GET only - nothing is filled, saved or sent.")
    print(f"Success threshold: >= {ESSF21_SUCCESS_MIN_BYTES:,} bytes "
          "(the browser measured 144,494; the known failure mode is 0)")
    print(f"Browser-like headers sent: {sorted(BROWSER_HEADERS.keys())} "
          "(Accept-Language is the one ESSF21 actually requires - see module docstring)")
    print(f"Output directory (gitignored) = {OUT_DIR}")

    results = [run_once(i) for i in range(1, RUNS + 1)]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    print(f"\n{'=' * 72}\nSummary\n{'=' * 72}")
    print(f"{'Run':4s} {'Outcome':18s} {'EPIE001':>10s} {'ESSF21':>10s} {'CL':>8s} "
          f"{'024':4s} {'VS':4s} {'Delay':>8s}")
    for r in results:
        epie = r.get("epie001", {})
        ess = r.get("essf21", {})
        mk = ess.get("markers", {})
        print(f"{r['run_index']:<4d} {r.get('outcome', '?'):18s} "
              f"{epie.get('bytes', 0):>10,} {ess.get('body_bytes', 0):>10,} "
              f"{str(ess.get('content_length_header', '-')):>8s} "
              f"{'Y' if mk.get('ESSCCDJ024_txt') else 'N':4s} "
              f"{'Y' if mk.get('__VIEWSTATE') else 'N':4s} "
              f"{str(r.get('elapsed_epie001_to_essf21_ms', '-')):>8s}")

    outcomes = [r.get("outcome") for r in results]
    n_full = outcomes.count("ESSF21_FULL")
    n_empty = outcomes.count("ESSF21_EMPTY_200")

    if n_full == RUNS:
        verdict = "PASS"
        msg = (f"{RUNS}/{RUNS} runs retrieved the full ESSF21 form - "
               "HTTP form access PASSES; plain HTTP can now read the real form reliably.")
    elif n_empty == RUNS:
        verdict = "ALL_EMPTY_200"
        msg = (f"{RUNS}/{RUNS} runs returned 200 with 0 bytes - CollectData initialization "
               "fixed EPIE001 but not ESSF21. Stopping without POSTing; the next step is "
               "a header/state comparison.")
    else:
        verdict = "INCONCLUSIVE"
        msg = (f"Mixed results (full {n_full} / empty {n_empty} / other "
               f"{RUNS - n_full - n_empty}) - marking INCONCLUSIVE rather than retrying "
               "until something succeeds.")

    print(f"\nVerdict: {verdict}\nReason : {msg}")
    (OUT_DIR / "verdict.json").write_text(
        json.dumps({"verdict": verdict, "explanation": msg, "outcomes": outcomes},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nResults written to {OUT_DIR / 'results.json'} and {OUT_DIR / 'verdict.json'}")


if __name__ == "__main__":
    main()
