"""Passive browser-side network capture - Experiments A/B/C/D.

Attaches to the user's already-logged-in Edge via the existing,
UNMODIFIED browser.attach_context(), verifies the session is
AUTHENTICATED via the existing, UNMODIFIED session.check_session(),
then clicks "出差登記" (reusing eip_client's own selector/text
constants, but with a locally-implemented click+wait so this script
can take cookie snapshots at intermediate points - eip_client.py
itself is never imported for mutation, only for its constants).

Explicitly out of scope, matching the user's own instructions:
- Never calls trip_form.fill_form / add_traveler / submit_form -
  nothing is filled, saved, or sent.
- Never issues a POST itself. This script only clicks one link and
  passively records whatever the SITE's own JS/postbacks do in
  response - it does not decide to POST anything.
- Never modifies src/eip_client.py, src/trip_form.py or
  src/network_log.py - those back the real, working submission flow.

Masking rules (stricter than network_log.py's, since this captures much
more detail per request):
- Cookie / Set-Cookie / Authorization header VALUES: never read, never
  logged - only "is this header present" (bool) is recorded.
- Cookie snapshots (Experiment C): name / domain / path / secure /
  httpOnly / sameSite only, via context.cookies() - the `value` field
  from that API is deliberately dropped before anything is saved.
- Query-string values for Identifier / LoginId / ClientIP (the fields
  the user identified as session-bound or personal): replaced with
  "<存在，長度=N，sha256前8碼=XXXXXXXX>". Every other query parameter
  name (TaskId, AFormType, AFormStatus, ProductName, FormID, Product)
  is a static routing constant, not sensitive, and is kept as-is.
- POST field values: never read - only field name, value length, and a
  coarse heuristic value "type" (empty/numeric/base64-like/long-text/
  short-text), same philosophy as trip_form's existing network logging.
- Raw HTML snapshots (for Experiment D's keyword search) are saved to
  logs/browser_capture/ (already gitignored via the existing "logs/"
  entry) for local, offline analysis only - never printed to console,
  never embedded verbatim in generated docs.

Run (after making sure you're logged into EIP in a debug-enabled Edge -
see README.md "執行 Phase 1 探索" 第一步, or just run this and follow
the printed manual-launch instructions if it can't attach automatically):

    python scripts/capture_browser_sequence.py
"""
import hashlib
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from playwright.sync_api import sync_playwright  # noqa: E402

import browser as browser_mod  # noqa: E402
import eip_client  # noqa: E402
from session import SessionState, check_session  # noqa: E402

OUT_DIR = ROOT / "logs" / "browser_capture"

SENSITIVE_QUERY_PARAMS = {"identifier", "loginid", "clientip"}

MARKERS = [
    "framePlus", "hdnplusFrameUrl", "hdnUniqueTaskId", "Identifier",
    "ProductIdentifier", "ProductUniversalID", "ProductFormID", "ProductParameters",
    "universalID", "TaskId", "FormID", "createTab", "src=", "location",
    "window.open", "document.write", "ajax", "$.ajax", "fetch", "__doPostBack",
]


def _summarize_sensitive(value: str) -> str:
    if not value:
        return "<空值>"
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:8]
    return f"<存在，長度={len(value)}，sha256前8碼={digest}>"


def _summarize_url(url: str) -> dict:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    names = [k for k, _ in pairs]
    values = {
        k: (_summarize_sensitive(v) if k.lower() in SENSITIVE_QUERY_PARAMS else v)
        for k, v in pairs
    }
    return {"base_url": base, "query_param_names": names, "query_param_values": values}


def _classify_value(value: str) -> str:
    if not value:
        return "empty"
    if value.isdigit():
        return "numeric"
    if len(value) > 40 and re.fullmatch(r"[A-Za-z0-9+/=]+", value):
        return "base64-like/blob"
    if len(value) > 200:
        return "long-text/blob"
    return "short-text"


def _post_field_summary(post_data) -> list:
    if not post_data:
        return []
    try:
        pairs = parse_qsl(post_data, keep_blank_values=True)
    except Exception:  # noqa: BLE001
        return [{"name": "<unparseable>", "value_length": len(post_data), "value_type": "unknown"}]
    return [
        {"name": name, "value_length": len(value), "value_type": _classify_value(value)}
        for name, value in pairs
    ]


def _cookie_snapshot(context) -> list:
    return [
        {
            "name": c["name"],
            "domain": c["domain"],
            "path": c["path"],
            "secure": c.get("secure", False),
            "httpOnly": c.get("httpOnly", False),
            "sameSite": c.get("sameSite", ""),
        }
        for c in context.cookies()
    ]


def _save_json(name: str, obj) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def _save_text(name: str, text: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(text, encoding="utf-8", errors="replace")


@dataclass
class SeqEvent:
    seq: int
    timestamp: float
    phase: str
    kind: str  # "request" | "response" | "requestfailed"
    method: str = ""
    base_url: str = ""
    query_param_names: list = field(default_factory=list)
    query_param_values: dict = field(default_factory=dict)
    status: int | None = None
    resource_type: str = ""
    frame_name: str = ""
    frame_url: str = ""
    referer: str = ""
    origin: str = ""
    request_content_type: str = ""
    response_content_type: str = ""
    response_content_length_header: str = ""
    response_body_length: int | None = None
    post_fields: list = field(default_factory=list)
    has_cookie_header: bool = False
    has_authorization_header: bool = False
    response_sets_cookie: bool = False
    initiator_type: str = ""
    initiator_url: str = ""
    redirected_from: str = ""
    note: str = ""
    failure: str = ""


class SequenceRecorder:
    """Attach for the whole click-to-ESSF21 window. `phase` is a plain
    attribute the caller mutates between the three observation windows
    (before/during/after) - events are stamped with whatever phase was
    current at the moment they fired."""

    def __init__(self):
        self.events: list[SeqEvent] = []
        self._seq = 0
        self._page = None
        self._cdp = None
        self._initiators = {}
        self.phase = "before_click"

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _on_cdp_request(self, params) -> None:
        try:
            url = (params.get("request") or {}).get("url", "")
            initiator = params.get("initiator") or {}
            self._initiators[url] = (initiator.get("type", ""), initiator.get("url", ""))
        except Exception:  # noqa: BLE001
            pass

    def _on_request(self, request) -> None:
        summary = _summarize_url(request.url)
        try:
            headers = request.headers
        except Exception:  # noqa: BLE001
            headers = {}
        init_type, init_url = self._initiators.get(request.url, ("", ""))
        frame = request.frame
        redirected_from = ""
        try:
            prev = request.redirected_from
            if prev is not None:
                redirected_from = _summarize_url(prev.url)["base_url"]
        except Exception:  # noqa: BLE001
            pass
        self.events.append(
            SeqEvent(
                seq=self._next_seq(),
                timestamp=time.time(),
                phase=self.phase,
                kind="request",
                method=request.method,
                base_url=summary["base_url"],
                query_param_names=summary["query_param_names"],
                query_param_values=summary["query_param_values"],
                resource_type=request.resource_type,
                frame_name=(frame.name if frame else ""),
                frame_url=(frame.url if frame else ""),
                referer=headers.get("referer", ""),
                origin=headers.get("origin", ""),
                request_content_type=headers.get("content-type", ""),
                post_fields=_post_field_summary(getattr(request, "post_data", None)),
                has_cookie_header="cookie" in headers,
                has_authorization_header="authorization" in headers,
                initiator_type=init_type,
                initiator_url=init_url,
                redirected_from=redirected_from,
            )
        )

    def _on_response(self, response) -> None:
        try:
            headers = response.headers
        except Exception:  # noqa: BLE001
            headers = {}
        try:
            body_len = len(response.body())
        except Exception:  # noqa: BLE001
            body_len = None
        summary = _summarize_url(response.url)
        frame = response.frame
        self.events.append(
            SeqEvent(
                seq=self._next_seq(),
                timestamp=time.time(),
                phase=self.phase,
                kind="response",
                method=response.request.method,
                base_url=summary["base_url"],
                query_param_names=summary["query_param_names"],
                query_param_values=summary["query_param_values"],
                status=response.status,
                resource_type=response.request.resource_type,
                frame_name=(frame.name if frame else ""),
                frame_url=(frame.url if frame else ""),
                response_content_type=headers.get("content-type", ""),
                response_content_length_header=headers.get("content-length", ""),
                response_body_length=body_len,
                has_cookie_header="cookie" in headers,
                response_sets_cookie="set-cookie" in headers,
            )
        )

    def _on_request_failed(self, request) -> None:
        summary = _summarize_url(request.url)
        frame = request.frame
        self.events.append(
            SeqEvent(
                seq=self._next_seq(),
                timestamp=time.time(),
                phase=self.phase,
                kind="requestfailed",
                method=request.method,
                base_url=summary["base_url"],
                query_param_names=summary["query_param_names"],
                query_param_values=summary["query_param_values"],
                resource_type=request.resource_type,
                frame_name=(frame.name if frame else ""),
                frame_url=(frame.url if frame else ""),
                failure=str(getattr(request, "failure", "") or ""),
            )
        )

    def attach(self, page) -> "SequenceRecorder":
        self._page = page
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)
        try:
            self._cdp = page.context.new_cdp_session(page)
            self._cdp.send("Network.enable")
            self._cdp.on("Network.requestWillBeSent", self._on_cdp_request)
        except Exception as e:  # noqa: BLE001
            print(f"  [note] 無法啟用 CDP Network 事件，initiator 欄位這次會是空的：{e}")
            self._cdp = None
        return self

    def detach(self) -> None:
        if self._page is None:
            return
        self._page.remove_listener("request", self._on_request)
        self._page.remove_listener("response", self._on_response)
        self._page.remove_listener("requestfailed", self._on_request_failed)
        if self._cdp is not None:
            try:
                self._cdp.detach()
            except Exception:  # noqa: BLE001
                pass
        self._page = None


def _click_trip_registration(page) -> None:
    banner = None
    for f in page.frames:
        if "titlebar1.aspx" in f.url:
            banner = f
            break
    if banner is None:
        raise RuntimeError("找不到 banner frame（titlebar1.aspx）")
    try:
        banner.locator(eip_client.TRIGGER_SELECTOR).click(timeout=5000)
        return
    except Exception:  # noqa: BLE001
        pass
    candidates = banner.get_by_text(eip_client.TRIGGER_TEXT, exact=False)
    if candidates.count() == 0:
        raise RuntimeError("找不到「出差登記」可點擊元素")
    candidates.first.click(timeout=5000)


def _wait_for_frame_containing(page, fragment: str, timeout_ms: int = 20000):
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        for f in page.frames:
            if fragment in f.url:
                return f
        page.wait_for_timeout(200)
    return None


def _run_experiment_b(events: list) -> list:
    print("\n=== Experiment B：EPIE001 回應 → ESSF21 請求之間的事件 ===")
    epie001_idx = None
    essf21_idx = None
    for i, e in enumerate(events):
        if epie001_idx is None and "EPIE001.aspx" in e["base_url"] and e["kind"] == "response":
            epie001_idx = i
        if essf21_idx is None and "ESSF21.aspx" in e["base_url"] and e["kind"] == "request":
            essf21_idx = i
    if epie001_idx is None or essf21_idx is None or essf21_idx <= epie001_idx:
        print("  無法在這次序列中同時定位到 EPIE001 回應與後續的 ESSF21 請求，略過。")
        _save_json("experiment_b_between_events.json", [])
        return []

    between = events[epie001_idx + 1 : essf21_idx]
    if not between:
        print("  兩者之間沒有任何其他事件 - ESSF21 的請求緊接在 EPIE001 回應之後。")
    else:
        print(f"  兩者之間共 {len(between)} 筆事件，全部標記為 POSSIBLE FORM INITIALIZATION：")
        for e in between:
            e["note"] = (e.get("note") or "").strip() + " POSSIBLE FORM INITIALIZATION"
            print(f"    seq={e['seq']} {e['kind']:14s} {e['method']:6s} {e['base_url']} status={e.get('status')}")
    _save_json("experiment_b_between_events.json", between)
    return between


def _run_experiment_d() -> dict:
    print("\n=== Experiment D：EPIE001 回應內容關鍵字搜尋 ===")
    path = OUT_DIR / "epie001_response.html"
    if not path.exists():
        print("  沒有存到 epie001_response.html，略過。")
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    results = {}
    for marker in MARKERS:
        count = text.count(marker)
        results[marker] = count
        if count:
            print(f"  {marker!r}: 出現 {count} 次")
    has_frame_tag_with_essf21 = bool(re.search(r"<i?frame[^>]*ESSF21\.aspx", text, re.IGNORECASE))
    results["_frame_tag_with_essf21_found"] = has_frame_tag_with_essf21
    print(f"\n  關鍵結論證據：HTML 是否有 <frame>/<iframe> 標籤直接帶 ESSF21.aspx：{has_frame_tag_with_essf21}")
    _save_json("experiment_d_markers.json", results)
    return results


def main():
    print("=== 被動觀察模式：不會填寫、不會儲存、不會送出任何表單 ===\n")

    with sync_playwright() as pw:
        try:
            br, context = browser_mod.attach_context(pw)
        except browser_mod.CdpConnectionError as e:
            print(f"[error] {e}")
            return

        page = eip_client.open_homepage(context)

        state = check_session(page)
        print(f"目前登入狀態：{state.value}")
        if state != SessionState.AUTHENTICATED:
            print("[stop] 不是 AUTHENTICATED，請先確認登入後再重新執行。")
            return

        if eip_client.find_trip_form_frame(page) is not None:
            print("[stop] 出差登記表單目前已經是開啟狀態，這次觀察不到「點擊前」的乾淨起點。"
                  "請先手動關閉該分頁籤（或重新整理首頁），再重新執行本腳本。")
            return

        print("\n=== Experiment C - 快照 1：點擊前 cookies ===")
        cookies_before = _cookie_snapshot(context)
        _save_json("cookies_before.json", cookies_before)
        print(f"  數量：{len(cookies_before)}，名稱：{[c['name'] for c in cookies_before]}")

        recorder = SequenceRecorder()
        recorder.attach(page)
        recorder.phase = "during_click_to_essf21"

        print("\n=== Experiment A - 點擊「出差登記」===")
        try:
            _click_trip_registration(page)
        except Exception as e:
            print(f"[error] 點擊失敗：{e}")
            recorder.detach()
            return

        print("等待 EPIE001.aspx frame 出現...")
        epie001_frame = _wait_for_frame_containing(page, "EPIE001.aspx", timeout_ms=15000)
        if epie001_frame is None:
            print("  [warn] 15 秒內沒等到 EPIE001.aspx。")
        else:
            print(f"  出現：{epie001_frame.url}")

        print("\n=== Experiment C - 快照 2：EPIE001 載入後 cookies ===")
        cookies_after_epie001 = _cookie_snapshot(context)
        _save_json("cookies_after_epie001.json", cookies_after_epie001)
        print(f"  數量：{len(cookies_after_epie001)}，名稱：{[c['name'] for c in cookies_after_epie001]}")

        print("\n等待 ESSF21.aspx frame 出現...")
        essf21_frame = _wait_for_frame_containing(page, "ESSF21.aspx", timeout_ms=20000)
        if essf21_frame is None:
            print("  [warn] 20 秒內沒等到 ESSF21.aspx - 這本身就是一個重要觀察結果（跟 HTTP POC 觀察到的不可重現現象一致），會如實記錄。")
        else:
            print(f"  出現：{essf21_frame.url}")
            try:
                has_target_field = essf21_frame.locator("#ESSCCDJ024_txt").count() > 0
            except Exception:  # noqa: BLE001
                has_target_field = False
            print(f"  ESSCCDJ024_txt 是否存在：{has_target_field}")

        recorder.phase = "after_essf21_confirmed"
        page.wait_for_timeout(500)  # let any trailing requests land before detaching
        recorder.detach()

        print("\n=== Experiment C - 快照 3：ESSF21 顯示後（或等待逾時後）cookies ===")
        cookies_after_essf21 = _cookie_snapshot(context)
        _save_json("cookies_after_essf21.json", cookies_after_essf21)
        print(f"  數量：{len(cookies_after_essf21)}，名稱：{[c['name'] for c in cookies_after_essf21]}")

        names_before = {c["name"] for c in cookies_before}
        names_mid = {c["name"] for c in cookies_after_epie001}
        names_after = {c["name"] for c in cookies_after_essf21}
        print(f"\n  點擊前 → EPIE001 後 新增的 cookie：{names_mid - names_before or '（無）'}")
        print(f"  EPIE001 後 → ESSF21 後 新增的 cookie：{names_after - names_mid or '（無）'}")

        for f in page.frames:
            if "EPIE001.aspx" in f.url:
                try:
                    _save_text("epie001_response.html", f.content())
                except Exception as e:  # noqa: BLE001
                    print(f"  [note] 無法讀取 EPIE001 frame content：{e}")
            if "ESSF21.aspx" in f.url:
                try:
                    _save_text("essf21_response.html", f.content())
                except Exception as e:  # noqa: BLE001
                    print(f"  [note] 無法讀取 ESSF21 frame content：{e}")

        events_dicts = [asdict(e) for e in recorder.events]
        _save_json("sequence.json", events_dicts)
        print(f"\n完整序列（{len(events_dicts)} 筆事件）已存到 {OUT_DIR / 'sequence.json'}")

        _run_experiment_b(events_dicts)
        _save_json("sequence.json", events_dicts)  # re-save with Experiment B's POSSIBLE FORM INITIALIZATION notes
        _run_experiment_d()

        print(f"\n完成。所有結果在 {OUT_DIR}（已 gitignore）。"
              "接下來請把這些結果交給 Claude 撰寫 docs/browser-vs-http-sequence.md。")


if __name__ == "__main__":
    main()
