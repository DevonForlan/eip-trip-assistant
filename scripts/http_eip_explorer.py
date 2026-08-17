"""HTTP + Windows SSPI explorer for EIP - GET-only research POC.

Evaluates whether EIP can be reached with `requests` + Windows SSPI
(`requests_negotiate_sspi`) instead of a real browser - i.e. whether the
`Edge + Playwright + CDP` login track can eventually be replaced by a
`Python + Windows SSPI + HTTP` track for the *login* step. This script
does not attempt to answer the *form submission* question - it only
GETs pages and reports what it finds.

Deliberately isolated from src/ (the working Playwright/CDP flow):
- No imports from src/ - this file is self-contained (stdlib + requests +
  requests_negotiate_sspi only) so it can be read and audited top to
  bottom on its own, especially since it handles auth headers.
- Never calls browser.py / eip_client.py / trip_form.py - nothing here
  can affect or be affected by the existing, working login/submit flow.
- GET only. No POST, anywhere, ever. This script cannot fill in or
  submit the trip form even if the URL is successfully derived.

Safety / masking rules (matches src/network_log.py's philosophy: when in
doubt, keep the field NAME and a LENGTH, never the VALUE):
- Authorization, Cookie and Set-Cookie headers: value replaced with
  "***MASKED***", never written to console, disk or docs/http-webforms-poc.md.
- WWW-Authenticate: only the auth SCHEME NAMES (e.g. "Negotiate", "NTLM")
  are extracted and reported - the raw header (which can carry a base64
  NTLM challenge blob) is never printed or saved.
- ASP.NET hidden fields (__VIEWSTATE, ProductIdentifier, ...): only
  presence + value length is reported, never the actual value.
- Raw HTML snapshots are saved under logs/http_explorer/ (already
  gitignored via the existing "logs/" entry) purely for manual follow-up
  reading - they are not printed to the console or embedded in docs.

Run:
    python scripts/http_eip_explorer.py
"""
import html.parser
import json
import os
import sys
from pathlib import Path
from urllib.parse import urljoin

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import requests
    from dotenv import load_dotenv
    from requests_negotiate_sspi import HttpNegotiateAuth
except ImportError as e:  # noqa: BLE001
    print(
        "[error] Missing dependency. Run:"
        "\n  pip install -r requirements.txt"
        f"\n(original error: {e})"
    )
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "logs" / "http_explorer"

load_dotenv(ROOT / ".env")

EIP_URL = os.environ.get("EIP_URL", "http://eip.example.com/EFNET/")
EIP_HOST = EIP_URL.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]

TIMEOUT_SECONDS = 15

SENSITIVE_HEADER_NAMES = {"authorization", "cookie", "set-cookie"}

# Target fields from the user's own field/selector table (docs/eip-analysis.md
# section 8) - checked for PRESENCE only, never read for value.
TARGET_FORM_FIELDS = [
    "ESSCCDJ024_txt",
    "ESSCCDJ025_txt",
    "ESSCCDJ026_txt",
    "ESSCCDJ027_txt",
    "ESSCCDJ028_txt",
    "ESSCCDJ037_txt",
    "ESSCCDJ029_txt",
    "ESSCCDD005_txt",
]
WEBFORMS_HIDDEN_FIELDS = [
    "__VIEWSTATE",
    "__VIEWSTATEGENERATOR",
    "__EVENTVALIDATION",
    "__EVENTTARGET",
    "__EVENTARGUMENT",
]


def _mask_headers(headers) -> dict:
    return {
        k: ("***MASKED***" if k.lower() in SENSITIVE_HEADER_NAMES else v)
        for k, v in headers.items()
    }


def _auth_schemes(www_authenticate_value: str) -> list:
    """Extract only the scheme tokens (e.g. "Negotiate", "NTLM") from a
    WWW-Authenticate header - never returns/keeps the raw value, which can
    carry a base64-encoded NTLM challenge blob."""
    if not www_authenticate_value:
        return []
    schemes = []
    for part in www_authenticate_value.split(","):
        token = part.strip().split(" ", 1)[0].strip()
        if token and token not in schemes:
            schemes.append(token)
    return schemes


def _len_or_none(value):
    if value is None:
        return None
    return len(value) if value else 0


class _PageParser(html.parser.HTMLParser):
    """Collects just enough structure to answer Phase 2's questions:
    frame/iframe tree edges, hidden-field presence (name -> length only,
    never value), and every input/textarea/select element id (for
    presence checks against TARGET_FORM_FIELDS)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.frames = []  # [{tag, name, src, id}]
        self.hidden_field_lengths = {}  # name -> len(value)
        self.element_ids = set()

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag in ("frame", "iframe"):
            self.frames.append(
                {
                    "tag": tag,
                    "name": d.get("name", ""),
                    "src": d.get("src", ""),
                    "id": d.get("id", ""),
                }
            )
        elif tag == "input":
            eid = d.get("id") or d.get("name") or ""
            if eid:
                self.element_ids.add(eid)
            if (d.get("type") or "").lower() == "hidden":
                name = d.get("name") or d.get("id") or ""
                if name:
                    self.hidden_field_lengths[name] = len(d.get("value") or "")
        elif tag in ("textarea", "select"):
            eid = d.get("id") or d.get("name") or ""
            if eid:
                self.element_ids.add(eid)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def _parse(html_text: str) -> _PageParser:
    parser = _PageParser()
    parser.feed(html_text)
    return parser


def _save_html(name: str, text: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(text, encoding="utf-8", errors="replace")


def _get_summary(session, url: str, save_as: str | None = None) -> dict:
    """GET url, return a masked/summarized result dict. Never raises -
    network/SSPI failures are captured as {"error": "..."} so one bad
    step doesn't abort the whole exploration run."""
    try:
        resp = session.get(url, timeout=TIMEOUT_SECONDS, allow_redirects=True)
    except requests.RequestException as e:
        return {"requested_url": url, "error": str(e)}

    parser = _parse(resp.text)
    if save_as:
        _save_html(save_as, resp.text)

    return {
        "requested_url": url,
        "final_url": resp.url,
        "status": resp.status_code,
        "content_type": resp.headers.get("Content-Type", ""),
        "content_length": len(resp.content),
        "title": parser.title.strip(),
        "redirect_chain": [f"{h.status_code} {h.url}" for h in resp.history],
        "headers_masked": _mask_headers(dict(resp.headers)),
        "_parser": parser,  # not JSON-serialized directly; consumed by caller
    }


def step0_anonymous_probe() -> dict:
    print("=== Step 0: anonymous GET, to see which auth schemes the server offers ===")
    try:
        resp = requests.get(EIP_URL, timeout=TIMEOUT_SECONDS, allow_redirects=True)
    except requests.RequestException as e:
        print(f"  [error] {e}")
        return {"error": str(e)}

    schemes = _auth_schemes(resp.headers.get("WWW-Authenticate", ""))
    result = {
        "status": resp.status_code,
        "final_url": resp.url,
        "auth_schemes_offered": schemes,
    }
    print(f"  status: {resp.status_code}")
    print(f"  auth schemes offered (scheme names only, never the raw header): "
          f"{schemes or '(no WWW-Authenticate header)'}")
    return result


def step1_authenticated_homepage(session) -> dict:
    print("\n=== Step 1: GET the homepage, authenticated via Windows SSPI ===")
    result = _get_summary(session, EIP_URL, save_as="step1_homepage.html")
    parser = result.pop("_parser", None)
    if "error" in result:
        print(f"  [error] {result['error']}")
        return result

    print(f"  status    : {result['status']}")
    print(f"  final URL : {result['final_url']}")
    print(f"  Content-Type：{result['content_type']}")
    print(f"  title     : {result['title']!r}")
    print(f"  length    : {result['content_length']} bytes")
    print(f"  redirects : {result['redirect_chain'] or '(none)'}")
    print(f"  headers (sensitive ones masked) and raw HTML written to {OUT_DIR}")

    result["frame_count"] = len(parser.frames) if parser else 0
    result["_final_url_for_crawl"] = result["final_url"]
    return result


def step2_crawl_frames(session, start_url: str, max_depth: int = 4, max_nodes: int = 60) -> list:
    print("\n=== Step 2: walk the frame/iframe tree from the homepage ===")
    visited = set()
    nodes = []
    queue = [(start_url, 0, "(root)")]
    truncated = False

    while queue:
        if len(nodes) >= max_nodes:
            truncated = True
            break
        url, depth, name = queue.pop(0)
        if url in visited or depth > max_depth or url.startswith("about:"):
            continue
        visited.add(url)

        node = {"depth": depth, "name": name, "url": url}
        try:
            resp = session.get(url, timeout=TIMEOUT_SECONDS, allow_redirects=True)
            parser = _parse(resp.text)
            node["status"] = resp.status_code
            node["final_url"] = resp.url
            node["title"] = parser.title.strip()
            node["child_frame_count"] = len(parser.frames)
            for fr in parser.frames:
                src = fr.get("src") or ""
                if not src or src.startswith("about:"):
                    continue
                child_url = urljoin(resp.url, src)
                queue.append((child_url, depth + 1, fr.get("name") or fr.get("id") or "(unnamed)"))
        except requests.RequestException as e:
            node["error"] = str(e)
        nodes.append(node)

    if truncated:
        print(f"  [note] Hit the {max_nodes}-node cap; some frames may be uncrawled. "
              "That means 'not visited', not 'not present'.")

    for n in nodes:
        indent = "  " * (n["depth"] + 1)
        if "error" in n:
            print(f"{indent}- {n['name']}: {n['url']}  [error] {n['error']}")
        else:
            print(f"{indent}- {n['name']}: {n.get('final_url', n['url'])}"
                  f"  (status={n.get('status')}, title={n.get('title')!r}, child_frames={n.get('child_frame_count')})")

    flags = {
        "found_platform_aspx": any("platform.aspx" in n.get("final_url", n["url"]) for n in nodes),
        "found_epie001_aspx": any("EPIE001.aspx" in n.get("final_url", n["url"]) for n in nodes),
        "found_essf21_aspx": any("ESSF21.aspx" in n.get("final_url", n["url"]) for n in nodes),
        "node_count": len(nodes),
        "truncated": truncated,
    }
    print(f"\n  found platform.aspx: {flags['found_platform_aspx']}")
    print(f"  found EPIE001.aspx : {flags['found_epie001_aspx']}")
    print(f"  found ESSF21.aspx  : {flags['found_essf21_aspx']}"
          " (expected False - that frame is injected by JS after the user clicks the\n"
          "  trip-registration shortcut, and a plain HTTP crawl runs no JS)")

    return nodes, flags


def step3a_bare_get(session) -> dict:
    print("\n=== Step 3a: GET the bare ESSF21 path (expected to lack required params) ===")
    bare_url = f"http://{EIP_HOST}/HRMESS/src/ESS/ESSF21/ESSF21.aspx"
    result = _get_summary(session, bare_url, save_as="step3a_bare.html")
    result.pop("_parser", None)
    if "error" in result:
        print(f"  [error] {result['error']}")
    else:
        print(f"  status: {result['status']}, final URL: {result['final_url']}, "
              f"title: {result['title']!r}")
    return result


def step3b_derive_from_wrapper(session) -> tuple:
    print("\n=== Step 3b: derive the ESSF21 URL from the stable EPIE001.aspx entry point ===")
    wrapper_url = f"http://{EIP_HOST}/EFNET/src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21"
    result = _get_summary(session, wrapper_url, save_as="step3b_epie001.html")
    parser = result.pop("_parser", None)

    if "error" in result:
        print(f"  [error] {result['error']}")
        return result, None

    print(f"  status: {result['status']}, final URL: {result['final_url']}, "
          f"title: {result['title']!r}")

    derived_url = None
    if parser:
        essf21_frames = [fr for fr in parser.frames if "ESSF21.aspx" in (fr.get("src") or "")]
        product_fields = {
            k: v for k, v in parser.hidden_field_lengths.items() if k.startswith("Product")
        }
        result["product_hidden_field_lengths"] = product_fields
        result["found_essf21_frame_directly"] = bool(essf21_frames)
        print(f"  Product* hidden fields (lengths only, never values): {product_fields or '(none)'}")
        if essf21_frames:
            derived_url = urljoin(result["final_url"], essf21_frames[0]["src"])
            result["derived_essf21_url_source"] = "found a <frame src> pointing at ESSF21.aspx in the EPIE001 response"
            print("  Found a frame in the EPIE001 response pointing at ESSF21.aspx - the "
                  "URL is derived from the real response, not hardcoded.")
        else:
            print("  No frame/iframe pointing at ESSF21.aspx in the EPIE001 response.")
            print("  (So framePlus is most likely assembled by this page's own JavaScript\n"
                  "   in the browser. A plain GET runs no JS, so the chain stops here -\n"
                  "   the URL is not guessed.)")
    return result, derived_url


def step3c_get_derived_form(session, derived_url: str) -> dict:
    print("\n=== Step 3c: GET the derived URL and check which fields are present ===")
    if not derived_url:
        print("  Step 3b derived no URL, and guessing one is not allowed. Skipping.")
        return {"skipped": True, "reason": "no derived url from step 3b"}

    result = _get_summary(session, derived_url, save_as="step3c_essf21.html")
    parser = result.pop("_parser", None)
    if "error" in result:
        print(f"  [error] {result['error']}")
        return result

    print(f"  status: {result['status']}, final URL: {result['final_url']}, "
          f"title: {result['title']!r}")

    if parser:
        target_presence = {f: (f in parser.element_ids) for f in TARGET_FORM_FIELDS}
        webforms_presence = {
            f: parser.hidden_field_lengths.get(f) for f in WEBFORMS_HIDDEN_FIELDS
        }
        result["target_field_presence"] = target_presence
        result["webforms_hidden_field_lengths"] = webforms_presence

        print("  Target field presence (presence only - values are never read):")
        for f, present in target_presence.items():
            print(f"    {f}: {'present' if present else 'absent'}")
        print("  ASP.NET WebForms hidden state fields (lengths only, never values):")
        for f, length in webforms_presence.items():
            print(f"    {f}: {'absent' if length is None else f'present, length {length}'}")

    return result


def main():
    print(f"EIP_URL = {EIP_URL}")
    print(f"EIP_HOST = {EIP_HOST}")
    print(f"Output directory for HTML snapshots (gitignored) = {OUT_DIR}\n")

    findings = {"eip_url": EIP_URL, "eip_host": EIP_HOST}

    findings["step0"] = step0_anonymous_probe()

    session = requests.Session()
    session.auth = HttpNegotiateAuth()

    findings["step1"] = step1_authenticated_homepage(session)
    if "error" in findings["step1"]:
        print("\n[stop] Step 1 failed; the later steps cannot run.")
        _dump_findings(findings)
        return

    nodes, flags = step2_crawl_frames(session, findings["step1"]["_final_url_for_crawl"])
    findings["step2"] = {"nodes": nodes, "flags": flags}

    findings["step3a"] = step3a_bare_get(session)

    step3b_result, derived_url = step3b_derive_from_wrapper(session)
    findings["step3b"] = step3b_result

    findings["step3c"] = step3c_get_derived_form(session, derived_url)

    _dump_findings(findings)
    print(f"\nStructured results (sensitive fields masked or reduced to lengths) "
          f"written to {OUT_DIR / 'findings.json'}")


def _dump_findings(findings: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items() if not k.startswith("_")}
        if isinstance(obj, list):
            return [_clean(v) for v in obj]
        return obj

    (OUT_DIR / "findings.json").write_text(
        json.dumps(_clean(findings), ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
