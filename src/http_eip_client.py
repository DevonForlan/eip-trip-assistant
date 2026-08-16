"""Reach the EIP 出差登記 (ESSF21) form over plain HTTP + Windows SSPI.

This is the HTTP track. It does not import, modify, or depend on the
Playwright/CDP track (browser.py / eip_client.py / trip_form.py), which
stays the working, unchanged fallback.

Two non-obvious conditions make this work, both established
experimentally rather than assumed - see docs/http-essf21-access-solved.md
and docs/http-epie001-init-condition.md:

1. CollectData.aspx must be GETted in the same session before EPIE001.
   Skip it and EPIE001 returns a 15,275-byte slim page with no link to
   ESSF21 at all. Notably, having an ASP.NET_SessionId is NOT sufficient:
   GETting TreeMainFrame.aspx also mints a session id, yet still yields
   the slim page. (Reproduced 5/5 vs 4/4.)

2. Accept-Language must be sent, or ESSF21 answers 200 with a zero-length
   body and no Content-Type header at all - the page carries an
   I18NLanguageType field and evidently gives up rendering when it cannot
   determine a language. Referer, Accept, Sec-Fetch-* and cookie scoping
   were each ruled out by leave-one-out testing. User-Agent is not
   required for access, but without a browser UA the response drops to
   ~137KB and omits __EVENTTARGET, which any future postback needs - so
   one is sent here too.

Nothing is hardcoded that can go stale: the CollectData URL is resolved
from the homepage's own frame src, and the ESSF21 URL (carrying a
per-request Identifier) is parsed from that run's EPIE001 response. No
Identifier, session id, or fully-formed ESSF21 URL is ever baked in.

Phase 3A is GET-only, and that is enforced in code rather than by
convention: the session refuses post/put/patch/delete unless the caller
explicitly opts out of read_only. Flipping that flag is a deliberate
Phase 3B decision, not something that can happen by accident.
"""
import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from requests_negotiate_sspi import HttpNegotiateAuth

from config import EIP_URL  # noqa: F401 - re-exported for existing callers

TRIP_WRAPPER_PATH = "src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21"

DEFAULT_TIMEOUT = 60
"""60s, not the usual few seconds: the full-version EPIE001 path was
observed to block transiently (3.7s, then >20s three times, then 0.4s),
and a short ceiling would misreport that as "the server returned the slim
page" - two situations needing opposite responses."""

BROWSER_HEADERS = {
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ),
}

SESSION_COOKIE = "ASP.NET_SessionId"

# Below this, EPIE001 returned the slim page (15,275 bytes observed
# repeatedly, byte-identical); the full page has measured 91,698-97,074.
WRAPPER_FULL_MIN_BYTES = 50_000
# The real form has measured 144,499-144,504 bytes; the failure mode is 0.
FORM_MIN_BYTES = 50_000

# Presence of all three is what "the form actually rendered" means here,
# rather than trusting a 200 or a byte count alone.
FORM_REQUIRED_MARKERS = ("ESSCCDJ024_txt", "__VIEWSTATE", "__EVENTTARGET")


class HttpEipError(RuntimeError):
    pass


class NotInitializedError(HttpEipError):
    pass


class SlimWrapperError(HttpEipError):
    """EPIE001 returned the slim page - the CollectData step did not take
    effect for this session."""


class FormNotRenderedError(HttpEipError):
    """ESSF21 responded but without real form content."""


class ReadOnlyViolation(HttpEipError):
    """A mutating HTTP method was attempted on a read-only session."""


class _GetOnlySession(requests.Session):
    """Blocks mutating verbs outright. Phase 3A must not POST, and a
    guard that fails loudly beats a comment asking people not to."""

    def _refuse(self, verb: str):
        raise ReadOnlyViolation(
            f"這個 HttpEipClient 是唯讀模式，拒絕執行 {verb}。"
            "若要進入會改變伺服器狀態的階段，必須明確以 HttpEipClient(read_only=False) 建立，"
            "並且要先取得使用者同意。"
        )

    def post(self, *a, **kw):
        self._refuse("POST")

    def put(self, *a, **kw):
        self._refuse("PUT")

    def patch(self, *a, **kw):
        self._refuse("PATCH")

    def delete(self, *a, **kw):
        self._refuse("DELETE")


@dataclass
class TripFormPage:
    url: str
    html: str

    @property
    def byte_length(self) -> int:
        return len(self.html.encode("utf-8", errors="replace"))


def _frame_src_matching(html: str, base_url: str, needle: str):
    """Resolve the first frame/iframe src containing `needle`. Used so
    neither the CollectData nor the ESSF21 URL is ever hardcoded."""
    m = re.search(
        r'<i?frame[^>]+src="([^"]*' + re.escape(needle) + r'[^"]*)"',
        html,
        re.IGNORECASE,
    )
    if not m:
        return None
    return urljoin(base_url, m.group(1))


class HttpEipClient:
    """Walks EIP to the ESSF21 form. Steps are separate methods so a
    caller can inspect each stage, but they must run in order - each one
    raises NotInitializedError rather than silently doing the previous
    step, so a failure points at the stage that actually broke.
    """

    def __init__(self, base_url: str = EIP_URL, timeout: int = DEFAULT_TIMEOUT,
                 read_only: bool = True):
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        self.timeout = timeout
        self.read_only = read_only
        self.session = None
        self.collectdata_url = None
        self.wrapper_html = None
        self.wrapper_url = None
        self.form_page = None

    # --- step 1 -----------------------------------------------------
    def authenticate(self) -> "HttpEipClient":
        """Build the session. No credentials are involved or stored: SSPI
        uses the Windows identity this process already runs as."""
        self.session = _GetOnlySession() if self.read_only else requests.Session()
        self.session.auth = HttpNegotiateAuth()
        self.session.headers.update(BROWSER_HEADERS)
        return self

    def _get(self, url: str, **kw):
        if self.session is None:
            raise NotInitializedError("尚未呼叫 authenticate()。")
        kw.setdefault("timeout", self.timeout)
        return self.session.get(url, **kw)

    @property
    def has_session_cookie(self) -> bool:
        if self.session is None:
            return False
        return any(c.name == SESSION_COOKIE for c in self.session.cookies)

    # --- step 2 -----------------------------------------------------
    def initialize_efnet(self) -> "HttpEipClient":
        """GET the homepage, then the CollectData.aspx it points at. This
        is the step whose absence yields the slim EPIE001 page."""
        resp = self._get(self.base_url)
        resp.encoding = "utf-8"
        if resp.status_code != 200:
            raise HttpEipError(f"GET 首頁失敗：HTTP {resp.status_code}")

        self.collectdata_url = _frame_src_matching(resp.text, resp.url, "CollectData.aspx")
        if self.collectdata_url is None:
            raise HttpEipError(
                "首頁 HTML 裡找不到指向 CollectData.aspx 的 frame src。"
                "EIP 首頁結構可能已改版 - 這一步是取得完整版表單的必要初始化，不能略過。"
            )

        resp2 = self._get(self.collectdata_url, allow_redirects=True)
        if resp2.status_code != 200:
            raise HttpEipError(f"GET CollectData.aspx 失敗：HTTP {resp2.status_code}")
        return self

    # --- step 3 -----------------------------------------------------
    def open_trip_wrapper(self) -> str:
        """GET EPIE001 and confirm it's the full version (the one that
        contains a link to ESSF21)."""
        if self.collectdata_url is None:
            raise NotInitializedError("尚未呼叫 initialize_efnet()。")

        self.wrapper_url = urljoin(self.base_url, TRIP_WRAPPER_PATH)
        resp = self._get(self.wrapper_url)
        resp.encoding = "utf-8"
        size = len(resp.content)
        if size < WRAPPER_FULL_MIN_BYTES:
            raise SlimWrapperError(
                f"EPIE001 只回傳 {size:,} bytes（精簡版），代表 CollectData 初始化這次沒有生效。"
                "不要重試送出任何東西，請先確認初始化步驟。"
            )
        self.wrapper_html = resp.text
        return self.wrapper_html

    # --- step 4 -----------------------------------------------------
    def open_trip_form(self) -> TripFormPage:
        """Parse this run's ESSF21 URL out of the wrapper response and GET
        it. The URL carries a per-request Identifier, so it is never
        reused across runs."""
        if self.wrapper_html is None:
            raise NotInitializedError("尚未呼叫 open_trip_wrapper()。")

        url = _frame_src_matching(self.wrapper_html, self.wrapper_url, "ESSF21.aspx")
        if url is None:
            raise HttpEipError(
                "完整版 EPIE001 裡卻找不到 ESSF21 的 frame src - 不該發生，請人工檢查頁面。"
            )

        resp = self._get(url, headers={"Referer": self.wrapper_url}, allow_redirects=True)
        resp.encoding = "utf-8"
        size = len(resp.content)
        if size < FORM_MIN_BYTES:
            raise FormNotRenderedError(
                f"ESSF21 回傳 HTTP {resp.status_code} 但只有 {size:,} bytes。"
                "若是 0 bytes，最可能是請求少了 Accept-Language。"
            )

        missing = [m for m in FORM_REQUIRED_MARKERS if m not in resp.text]
        if missing:
            raise FormNotRenderedError(
                f"ESSF21 內容缺少必要標記：{missing}。"
                "（缺 __EVENTTARGET 通常代表沒有送出瀏覽器 User-Agent。）"
            )

        self.form_page = TripFormPage(url=resp.url, html=resp.text)
        return self.form_page

    # --- convenience ------------------------------------------------
    def prepare(self) -> TripFormPage:
        """Run all four steps in order and return the form page."""
        self.authenticate()
        self.initialize_efnet()
        self.open_trip_wrapper()
        return self.open_trip_form()
