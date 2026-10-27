"""Fill in and submit the EIP missed-punch (ESSF03 補刷卡申請) form.

Field ids verified against the live form (2026-10), not guessed:
- ESSBSK021 / ESSBSK022: the date the punch is for (start / end - always
  the same day here).
- ESSBSK023, 031..035: up to six punch times, in order.
- ESSBSK025: reason. It is a coded lookup, not free text - the id lives
  in ESSBSK024, and typing a name into ESSBSK025 fails validation with
  「補刷卡原因」欄位輸入錯誤. It has to be picked from the F2 picker
  (ESSBSK025_btn opens F2Single.aspx; a row is chosen by double-click).
- ESSBSK026: note.

Like the trip form, the fields live in one frame (ESS/ESSF03/ESSF03.aspx)
and the Send button in its wrapper (EPI/EPIE001/EPIE001.aspx?FormID=ESSF03).

submit_form() clicks a real, irreversible Send button - only call it
after the user has explicitly confirmed with `y` (see src/punch_main.py).
"""
import re
import time
from dataclasses import dataclass, field

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from dialog_handler import DialogRecorder
from eip_client import find_tree_frame, wait_for_platform_frame
from network_log import NetworkRecorder
from session import SessionState, check_session
from trip_form import LOG_DIR, SEND_BUTTON_SELECTOR, SEND_CLICK_TIMEOUT_MS, SubmissionResult

FORM_FRAME_FRAGMENT = "/ESSF03/ESSF03.aspx"
WRAPPER_FRAME_FRAGMENT = "EPIE001.aspx?FormID=ESSF03"
PICKER_FRAME_FRAGMENT = "F2Single.aspx"

DATE_FIELD_IDS = ("ESSBSK021_txt", "ESSBSK022_txt")
TIME_FIELD_IDS = ("ESSBSK023_txt", "ESSBSK031_txt", "ESSBSK032_txt",
                  "ESSBSK033_txt", "ESSBSK034_txt", "ESSBSK035_txt")
REASON_ID_FIELD_ID = "ESSBSK024_txt"
REASON_FIELD_ID = "ESSBSK025_txt"
REASON_BUTTON_ID = "ESSBSK025_btn"
NOTE_FIELD_ID = "ESSBSK026_txt"

# What the picker offers. HR's convention for a typhoon day worked from
# home: 其他, with a note like "10/23(五)颱風日居家辦公補打卡".
REASONS = ("忘記刷卡", "未發卡片", "其他")

# The form is opened the same way its menu entry does it: createTab() run
# inside the sidebar frame. A javascript: URL is used because the tree
# frame's own scope is where createTab is defined.
OPEN_TAB_JS = """() => { location.href = "javascript:createTab("
    + "'../../../EPI/EPIE001/EPIE001.aspx?FormID=ESSF03','ESSF03','補刷卡申請(ESSF03)','108')"; }"""

SUBMITTED_FRAME_URL_PATTERN = re.compile(r"SheetNo=(\d{6,})")

DATE_PATTERN = re.compile(r"^\d{4}/\d{2}/\d{2}$")
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class PunchValidationError(ValueError):
    pass


@dataclass
class PunchRequest:
    date: str
    times: list = field(default_factory=list)
    reason: str = "忘記刷卡"
    note: str = ""

    def validate(self) -> None:
        if not DATE_PATTERN.match(self.date):
            raise PunchValidationError(f"Date must look like 2026/10/16, got {self.date!r}")
        if not 1 <= len(self.times) <= len(TIME_FIELD_IDS):
            raise PunchValidationError(
                f"Between 1 and {len(TIME_FIELD_IDS)} times are needed, got {len(self.times)}")
        bad = [t for t in self.times if not TIME_PATTERN.match(t)]
        if bad:
            raise PunchValidationError(f"Times must look like 08:30, got {bad}")
        if self.reason not in REASONS:
            raise PunchValidationError(f"Reason must be one of {REASONS}, got {self.reason!r}")


def expected_values(req: PunchRequest) -> dict:
    """What every relevant field must read once the form is filled -
    including the unused time slots, which must stay empty."""
    expected = {fid: req.date for fid in DATE_FIELD_IDS}
    for i, fid in enumerate(TIME_FIELD_IDS):
        expected[fid] = req.times[i] if i < len(req.times) else ""
    expected[REASON_FIELD_ID] = req.reason
    expected[NOTE_FIELD_ID] = req.note
    return expected


def mismatches(req: PunchRequest, actual: dict) -> dict:
    """{field: (expected, actual)} for every field that does not read back
    as expected. A reason whose coded id is empty counts too: the name can
    show while the id the server actually checks is missing."""
    bad = {k: (v, actual.get(k)) for k, v in expected_values(req).items() if actual.get(k) != v}
    if not actual.get(REASON_ID_FIELD_ID):
        bad[REASON_ID_FIELD_ID] = ("<reason id>", actual.get(REASON_ID_FIELD_ID))
    return bad


def _frame_matching(page, fragment: str):
    for f in page.frames:
        if fragment in f.url:
            return f
    return None


def find_form_frame(page):
    return _frame_matching(page, FORM_FRAME_FRAGMENT)


def find_wrapper_frame(page):
    return _frame_matching(page, WRAPPER_FRAME_FRAGMENT)


def _form_is_ready(frame) -> bool:
    try:
        return bool(frame.evaluate(
            f"() => !!document.getElementById('{TIME_FIELD_IDS[0]}') "
            "&& document.readyState == 'complete'"))
    except Exception:  # noqa: BLE001 - a frame mid-navigation
        return False


def open_form(page, attempts: int = 3, wait_seconds: int = 25):
    """Open the missed-punch form in its own tab and wait for it to load.
    Returns the form frame.

    The tab sometimes never appears on the first try right after login,
    so the createTab call is repeated - only when no form frame exists
    yet, so a loaded form is never opened twice.
    """
    if wait_for_platform_frame(page) is None:
        raise RuntimeError("Timed out waiting for platform.aspx - the form's tab is created there.")
    for _ in range(attempts):
        if find_form_frame(page) is None:
            tree = find_tree_frame(page)
            if tree is None:
                raise RuntimeError("Sidebar frame (tree.aspx) not found.")
            tree.evaluate(OPEN_TAB_JS)
        for _ in range(wait_seconds):
            time.sleep(1)
            frame = find_form_frame(page)
            if frame is not None and _form_is_ready(frame):
                return frame
    raise TimeoutError("The missed-punch form never finished loading. Nothing was sent.")


def _set_value(frame, field_id: str, value: str) -> None:
    # Set and fire change/blur rather than fill(): the form's own
    # handlers reformat and cross-check on blur, and need a moment to run.
    frame.evaluate(
        """([id, v]) => { const e = document.getElementById(id);
            e.focus(); e.value = v;
            e.dispatchEvent(new Event('change', {bubbles: true})); e.blur(); }""",
        [field_id, value])
    time.sleep(1.5)


PICK_ROW_JS = """(name) => {
    const rows = Array.from(document.querySelectorAll('#dgdSingleChoose tr'))
        .filter(tr => Array.from(tr.cells).some(c => c.innerText.trim() == name));
    if (rows.length != 1) return rows.length;
    setTimeout(() => rows[0].dispatchEvent(new MouseEvent('dblclick', {bubbles: true})), 0);
    return 1;
}"""


def _pick_reason(page, frame, reason: str, seconds: int = 18) -> None:
    """Choose the reason from the F2 picker.

    Two timing traps, both observed: clicking the button while the time
    fields' blur handlers are still running opens nothing, hence the
    initial pause; and the first click can still be swallowed, hence
    re-clicking every six seconds while no picker is showing. The clicks
    are deferred with setTimeout because the picker opens modally and
    would otherwise block the evaluate call.
    """
    time.sleep(3)
    for i in range(seconds):
        if i % 6 == 0 and _frame_matching(page, PICKER_FRAME_FRAGMENT) is None:
            frame.evaluate(
                f"() => setTimeout(() => document.getElementById('{REASON_BUTTON_ID}').click(), 0)")
        time.sleep(1)
        picker = _frame_matching(page, PICKER_FRAME_FRAGMENT)
        if picker is None:
            continue
        try:
            if not picker.evaluate("() => !!document.getElementById('dgdSingleChoose')"):
                continue
            found = picker.evaluate(PICK_ROW_JS, reason)
        except Exception:  # noqa: BLE001 - picker still loading
            continue
        if found != 1:
            raise RuntimeError(f"Reason {reason!r} matched {found} picker rows. Nothing was sent.")
        time.sleep(2)
        return
    raise TimeoutError("The reason picker never opened. Nothing was sent.")


def fill_form(page, frame, req: PunchRequest) -> None:
    """Fill every field. Any dialog raised while filling (e.g. a
    validation alert) is dismissed and raised as UnexpectedDialogError."""
    recorder = DialogRecorder().attach(page)
    try:
        for fid in DATE_FIELD_IDS:
            _set_value(frame, fid, req.date)
        for fid, value in zip(TIME_FIELD_IDS, req.times):
            _set_value(frame, fid, value)
        if read_back(frame).get(REASON_FIELD_ID) != req.reason:
            _pick_reason(page, frame, req.reason)
        if req.note:
            _set_value(frame, NOTE_FIELD_ID, req.note)
    finally:
        recorder.detach()
    recorder.raise_if_unexpected()


def read_back(frame) -> dict:
    ids = [*DATE_FIELD_IDS, *TIME_FIELD_IDS, REASON_ID_FIELD_ID, REASON_FIELD_ID, NOTE_FIELD_ID]
    return frame.evaluate(
        "(ids) => Object.fromEntries(ids.map(i => [i, (document.getElementById(i) || {}).value]))",
        ids)


def submit_form(page) -> None:
    """Clicks the real Send button - a genuine, irreversible submission.
    Its confirms ("send the form?", "the punch date is YYYY/MM/DD?") are
    accepted by dialog_handler's policy; anything else is dismissed and
    raised. A click that times out is not retried - verify_submission
    reads the real outcome."""
    wrapper = find_wrapper_frame(page)
    if wrapper is None:
        raise RuntimeError("Wrapper frame (EPIE001.aspx?FormID=ESSF03) not found - cannot submit.")

    dialog_recorder = DialogRecorder()
    network_recorder = NetworkRecorder("send missed punch")
    dialog_recorder.attach(page)
    network_recorder.attach(page)
    try:
        try:
            wrapper.click(SEND_BUTTON_SELECTOR, timeout=SEND_CLICK_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            pass
        page.wait_for_timeout(1500)
    finally:
        dialog_recorder.detach()
        network_recorder.detach()
        network_recorder.save(LOG_DIR / f"submit_punch_{int(time.time())}.log")
    dialog_recorder.raise_if_unexpected()


def verify_submission(page, timeout_s: int = 30) -> tuple:
    """SUCCESS only when a frame shows the submitted document's number.
    Everything else is UNKNOWN - this form has not been seen failing
    visibly, so there is no FAILED signal to look for. On UNKNOWN, check
    the server (duplicate_check.wait_for_rows_via_http); never resend."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        for f in page.frames:
            match = SUBMITTED_FRAME_URL_PATTERN.search(f.url)
            if match:
                return SubmissionResult.SUCCESS, f"Document number: {match.group(1)}"
        if check_session(page) == SessionState.EXPIRED:
            return SubmissionResult.UNKNOWN, "The session ended during the send."
        time.sleep(1)
    return SubmissionResult.UNKNOWN, "Timed out without seeing a document number."
