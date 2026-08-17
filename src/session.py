"""Session health check for the EIP homepage/tab.

Needed because "does a page/tab matching example.com exist" (the old
check in eip_client.find_existing_page) is not the same question as "is
this tab actually still logged in" - ChromeADLogout.htm and the
the "Session過期" (session expired) page both still live under the
eip.example.com host, so
that substring match alone cannot tell an expired session from a live
one. Confirmed by hand during Phase 2 testing: a stale session
mid-postback redirected to ChromeADLogout.htm, and code that only
checked the URL fragment would have happily tried to keep operating on
a logged-out page.
"""
import time
from enum import Enum

LOGOUT_URL_FRAGMENT = "ChromeADLogout.htm"

EXPIRED_TEXT_MARKERS = (
    "Session過期",
    "session過期",
    "敬請重新登入",
    "請重新登入",
)

# Frames that are always present on a genuinely logged-in EIP homepage
# (see docs/eip-analysis.md section 1) - the classic frameset shell.
REQUIRED_HOME_FRAME_FRAGMENTS = (
    "titlebar1.aspx",
    "tree.aspx",
    "platform.aspx",
)


class SessionState(str, Enum):
    AUTHENTICATED = "AUTHENTICATED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


def _page_text(page) -> str:
    try:
        return page.evaluate("() => document.body ? document.body.innerText : ''") or ""
    except Exception:  # noqa: BLE001 - a page mid-navigation may not evaluate cleanly
        return ""


def check_session(page) -> SessionState:
    """Best-effort classification of the current page's login state.

    Callers MUST treat EXPIRED as a hard stop - never fill in or submit
    anything against a page in this state (see state_machine.py).
    UNKNOWN means "couldn't positively confirm either way" (e.g. page
    mid-navigation, or the frameset shape changed) - callers should
    treat this as not-safe-to-proceed too, just with a different message
    than an outright EXPIRED, since we don't actually know here.
    """
    if LOGOUT_URL_FRAGMENT in page.url:
        return SessionState.EXPIRED

    try:
        frame_urls = [f.url for f in page.frames]
    except Exception:  # noqa: BLE001
        frame_urls = []

    if any(LOGOUT_URL_FRAGMENT in u for u in frame_urls):
        return SessionState.EXPIRED

    body_text = _page_text(page)
    if any(marker in body_text for marker in EXPIRED_TEXT_MARKERS):
        return SessionState.EXPIRED

    if any(
        any(fragment in u for u in frame_urls)
        for fragment in REQUIRED_HOME_FRAME_FRAGMENTS
    ):
        return SessionState.AUTHENTICATED

    return SessionState.UNKNOWN


def wait_until_authenticated(page, timeout_ms: int = 10000) -> SessionState:
    """Poll check_session until it settles on something other than UNKNOWN.

    UNKNOWN genuinely means "cannot tell yet", and a frameset that is still
    assembling reads exactly that way - so an immediate verdict aborts runs
    over a page that was one second away from being fine. Seen three times
    in live use. EXPIRED is returned the moment it appears rather than
    waited on: that answer will not improve, and callers must stop on it.
    """
    deadline = time.time() + timeout_ms / 1000
    state = check_session(page)
    while state == SessionState.UNKNOWN and time.time() < deadline:
        page.wait_for_timeout(500)
        state = check_session(page)
    return state
