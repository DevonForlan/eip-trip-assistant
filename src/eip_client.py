"""Navigate the EIP portal and open the trip-registration form.

Verified in Phase 1 (see docs/eip-analysis.md):
- EIP requires Windows Integrated Auth that Playwright cannot complete on
  its own; `context` must come from browser.attach_context, which ensures
  VPN + a debug Edge launched with the EIP URL as a command-line argument
  (so NTLM SSO fires automatically) - never from a Playwright-navigated
  page.
- The trip-registration shortcut lives in the banner frame
  (titlebar1.aspx). That JS-injects a NEW iframe into the page rather
  than navigating, so the result is a new Frame, not a new Page/popup.
- The form fields live in one frame (ESS/ESSF21/ESSF21.aspx); the
  toolbar Send/Save buttons live in a DIFFERENT, wrapping frame
  (EPI/EPIE001/EPIE001.aspx). Callers must fetch whichever frame they
  need via the helpers below rather than assuming a single frame.
"""
import time

from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

from browser import find_existing_page
from config import EIP_HOST, EIP_URL  # noqa: F401 - EIP_URL re-exported

# Derived, never hardcoded: this is what find_existing_page() matches tabs
# against, so pinning it to a literal would silently stop matching the
# moment EIP_URL is pointed at a different host.
EIP_URL_FRAGMENT = EIP_HOST

TRIGGER_SELECTOR = "td#tdMenu_1 > table > tbody > tr > td:nth-of-type(2)"
TRIGGER_TEXT = "出差登記"
TRIP_FORM_FRAME_FRAGMENT = "ESS/ESSF21/ESSF21.aspx"
TRIP_FORM_WRAPPER_FRAME_FRAGMENT = "EPI/EPIE001/EPIE001.aspx"


def open_homepage(context):
    """Reuse the existing EIP tab in the attached Edge (it's already
    logged in via NTLM).

    Deliberately does NOT fall back to context.new_page().goto(EIP_URL):
    that's a CDP-driven navigation, and EIP's NTLM auth is confirmed to
    always fail for those (see browser.py module docstring) - even
    clicking a real link via Playwright hits the same
    ERR_INVALID_AUTH_CREDENTIALS, since the block applies to any
    navigation on a page Playwright is attached to, not just goto()
    specifically. So if the tab genuinely isn't there yet, this retries
    the lookup for a few seconds (browser.attach_context's own page-list
    sync can lag slightly) and then raises rather than attempting a
    navigation that is guaranteed to fail.
    """
    deadline = time.time() + 8
    while time.time() < deadline:
        page = find_existing_page(context, EIP_URL_FRAGMENT)
        if page is not None:
            return page
        time.sleep(0.5)

    raise RuntimeError(
        "No logged-in EIP tab found. The Edge that browser.attach_context launched "
        "never reached EIP - it may still be retrying, or stuck on an error page. "
        "Run this again, or launch Edge yourself using the command printed on failure "
        "and confirm you are logged in."
    )


def find_trip_form_frame(page):
    for f in page.frames:
        if TRIP_FORM_FRAME_FRAGMENT in f.url:
            return f
    return None


def find_trip_form_wrapper_frame(page):
    for f in page.frames:
        if TRIP_FORM_WRAPPER_FRAME_FRAGMENT in f.url:
            return f
    return None


def _find_banner_frame(page):
    for f in page.frames:
        if "titlebar1.aspx" in f.url:
            return f
    return None


def wait_for_banner_frame(page, timeout_ms: int = 10000):
    """Wait for the banner frame instead of demanding it be there already.

    The frameset assembles asynchronously, so right after the homepage
    loads (or reloads) page.frames can be missing titlebar1.aspx for a
    moment. Failing instantly on that produced a "the page may have changed" error for
    what was really just a page that had not finished settling - observed
    live, where an immediate retry succeeded with no other change.
    """
    deadline = time.time() + timeout_ms / 1000
    while True:
        banner = _find_banner_frame(page)
        if banner is not None:
            return banner
        if time.time() >= deadline:
            return None
        page.wait_for_timeout(300)


def _find_platform_frame(page):
    for f in page.frames:
        if "platform.aspx" in f.url:
            return f
    return None


# The trip-registration tab is a jQuery UI Tabs widget in platform.aspx - its
# anchor id is the ESS form code, verified by hand (not guessed) by
# walking up from the visible tab text to its containing <li>/<a>.
TRIP_FORM_TAB_ANCHOR_SELECTOR = "#ESSF21"


def reactivate_trip_form_tab(page, timeout_ms: int = 5000) -> bool:
    """Bring the already-open trip-registration tab back to the foreground.

    Needed because switching the sidebar into form-tracking mode (see
    duplicate_check.find_existing_submission) backgrounds whichever
    platform.aspx tab was active - its content becomes hidden
    (fails Playwright's visibility check), not just unfocused. Any
    caller that interacts with the trip form after checking for
    duplicates must call this first. Returns False (does not raise) if
    the tab anchor isn't there - callers should treat that as "the trip
    form may not be open here" rather than a hard error.
    """
    platform_frame = _find_platform_frame(page)
    if platform_frame is None:
        return False
    try:
        platform_frame.click(TRIP_FORM_TAB_ANCHOR_SELECTOR, timeout=timeout_ms)
        return True
    except (PlaywrightError, PlaywrightTimeoutError):
        return False


def has_trip_form_tab(page) -> bool:
    """Whether platform.aspx still shows a trip-registration tab, regardless of what
    that tab currently contains."""
    platform_frame = _find_platform_frame(page)
    if platform_frame is None:
        return False
    try:
        return bool(
            platform_frame.evaluate(
                "(sel) => !!document.querySelector(sel)", TRIP_FORM_TAB_ANCHOR_SELECTOR
            )
        )
    except (PlaywrightError, PlaywrightTimeoutError):
        return False


def close_trip_form_tab(page, timeout_ms: int = 10000) -> bool:
    """Close the trip-registration tab via its own close icon. Returns True once the
    tab is gone.

    Clicking the icon through the DOM rather than driving the underlying
    btClosejQTab control keeps this to exactly what a person clicking the
    little x would do.
    """
    platform_frame = _find_platform_frame(page)
    if platform_frame is None:
        return False
    try:
        clicked = platform_frame.evaluate(
            """(sel) => {
                const anchor = document.querySelector(sel);
                if (!anchor) return false;
                const li = anchor.closest('li');
                if (!li) return false;
                const closer = li.querySelector('.ui-icon-close');
                if (!closer) return false;
                closer.click();
                return true;
            }""",
            TRIP_FORM_TAB_ANCHOR_SELECTOR,
        )
    except (PlaywrightError, PlaywrightTimeoutError):
        return False
    if not clicked:
        return False

    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        if not has_trip_form_tab(page):
            return True
        page.wait_for_timeout(300)
    return False


def find_tree_frame(page):
    """The left-hand sidebar frame (tree.aspx) - hosts both the
    application-shortcut tree used by open_trip_form() and, after
    clicking the form-tracking button (#tdBar4), the folder tree used
    by duplicate_check.find_existing_submission()."""
    for f in page.frames:
        if "tree.aspx" in f.url:
            return f
    return None


def open_trip_form(page, timeout_ms: int = 25000, close_stale_tab: bool = True):
    """Click the trip-registration shortcut (if the form isn't already open) and
    wait for its content frame to finish loading.

    Returns `page`. The fields and the Send/Save buttons live in two
    different frames - use find_trip_form_frame(page) /
    find_trip_form_wrapper_frame(page) to reach the right one.

    close_stale_tab handles filing several trips in one session. After a
    successful send the trip-registration tab remains, but now shows the submitted
    document read-only (FlowChart.aspx), so there is no editable ESSF21
    frame any more. Clicking the shortcut in that state merely re-activates
    the existing tab, no new form loads, and this used to time out - which
    is what limited a run to one submission. Closing the spent tab first
    makes the shortcut build a fresh form.

    An editable form that is already open is always reused, never closed:
    the branch below returns before any of this, so a half-filled form
    cannot be discarded by accident. It is brought back to the foreground
    first, though - an earlier duplicate check may have switched the
    sidebar into form-tracking mode, which leaves the trip-form tab present
    but hidden, and callers would then hit "element is not visible" on the
    first fill.
    """
    if find_trip_form_frame(page) is not None:
        reactivate_trip_form_tab(page)
        page.wait_for_timeout(500)
        return page

    if close_stale_tab and has_trip_form_tab(page):
        close_trip_form_tab(page)
        page.wait_for_timeout(1000)

    banner = wait_for_banner_frame(page)
    if banner is None:
        raise RuntimeError(
            "Timed out waiting for the banner frame (titlebar1.aspx). If the page has "
            "only just loaded, retry shortly; if it keeps happening the page layout may "
            "have changed - re-run scripts/inspect_eip.py to check."
        )

    existing_frame_urls = {f.url for f in page.frames}

    clicked = False
    try:
        banner.locator(TRIGGER_SELECTOR).click(timeout=5000)
        clicked = True
    except (PlaywrightError, PlaywrightTimeoutError):
        pass
    if not clicked:
        candidates = banner.get_by_text(TRIGGER_TEXT, exact=False)
        if candidates.count() > 0:
            candidates.first.click(timeout=5000)
            clicked = True
    if not clicked:
        raise RuntimeError(
            "Trip-registration shortcut not found; the page layout may have changed - "
            "re-run scripts/inspect_eip.py to check."
        )

    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        frame = find_trip_form_frame(page)
        if frame is not None and frame.url not in existing_frame_urls:
            try:
                frame.wait_for_load_state("load", timeout=5000)
                frame.wait_for_load_state("networkidle", timeout=8000)
            except PlaywrightTimeoutError:
                pass
            return page
        page.wait_for_timeout(300)

    raise TimeoutError(
        "Clicked the trip-registration shortcut but the form never finished loading. "
        "Check the screen state by hand."
    )
