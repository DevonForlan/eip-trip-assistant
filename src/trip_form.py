"""Fill in and submit the EIP 出差登記 (ESSF21) form.

Field <-> id mapping was verified by hand in Phase 1, not guessed - see
docs/eip-analysis.md section 8. This form has NO transport-method field
(confirmed: the "彈性欄位" extra-field feature is disabled on this
tenant - its button is literally `disabled` with onclick
`alert('該作業尚未設定彈性欄位!')`), so trip.transport is folded into
the 備註 (note) field instead.

submit_form() clicks a real, irreversible "傳送" button - only call it
after the user has explicitly confirmed with `y` (see src/main.py).
"""
import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from dialog_handler import DialogRecorder
from eip_client import find_trip_form_frame, find_trip_form_wrapper_frame
from network_log import NetworkRecorder
from session import SessionState, check_session

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "logs"

FIELD_IDS = {
    "start_date": "ESSCCDJ024_txt",
    "start_time": "ESSCCDJ025_txt",
    "end_date": "ESSCCDJ026_txt",
    "end_time": "ESSCCDJ027_txt",
    "location": "ESSCCDJ028_txt",
    "reason": "ESSCCDJ037_txt",
    "note": "ESSCCDJ029_txt",
}

# 出差明細 grid - the "add a traveler" row. Verified by hand: the code
# field's own onblur calls CheckPeoplePower(code) and clears itself if
# invalid (see docs/eip-analysis.md section 9), so this fills the code
# and lets the site's own JS resolve the name, rather than guessing at
# a picker-popup flow.
DETAIL_PERSON_CODE_SELECTOR = "#ESSCCDD005_txt"
DETAIL_PERSON_NAME_SELECTOR = "#ESSCCDD006_txt"
DETAIL_SAVE_BUTTON_SELECTOR = "#GridUserControl1_Button9"

REQUIRED_FIELD_LABELS = {
    "start_date": "開始日期",
    "start_time": "開始時間",
    "end_date": "結束日期",
    "end_time": "結束時間",
    "location": "出差地點",
    "reason": "出差原因",
}

# Verified by reading the button's `title` attribute (no click involved):
# MasterPage_btnCreateToolSendForm -> title="傳送" (real submit).
# MasterPage_btnCreateToolSaveForm -> title="草稿儲存" (draft save, unused here).
SEND_BUTTON_SELECTOR = "#MasterPage_btnCreateToolSendForm"

# 填單人 code - always auto-filled by EIP to the logged-in user, never
# typed by us. Used as the default 出差人 (see get_filler_employee_code)
# since every real submission so far has the filer also be the
# traveler - a general "who else is traveling" flow is future work, not
# guessed at here.
FILLER_CODE_FIELD_ID = "ESSCCDJ004_txt"

DOC_NUMBER_FIELD_ID = "ESSCCDJ002_txt"  # 單號 - stays "AutoNumber" until a real send succeeds

# Confirmed pattern from three successful live submissions (2026-08-11,
# 2026-08-12, 2026-08-14) - a real send replaces the form view with an
# approval workflow diagram headed by this exact text, e.g.
# "單據:ESSF21 出差登記 (202601020001)". The number is a real, assigned
# document id, never "AutoNumber".
DOCUMENT_NUMBER_PATTERN = re.compile(r"單據[:：]\s*ESSF21\s*出差登記\s*\((\d+)\)")

# A second, structural success signal found on 2026-08-14: after a real
# send the form frame is replaced by FlowChart.aspx carrying the assigned
# document number and a read-only mode flag. Checking frame URLs is both
# cheaper and less brittle than scraping rendered text, and it survives the
# text not having painted yet - which is precisely what made that send
# report UNKNOWN despite having succeeded.
SUBMITTED_FRAME_URL_PATTERN = re.compile(r"SheetNo=(\d{6,})&ShowMode=ReadFormReadOnly")

# 8s was the original budget and it expired on a send that had in fact
# gone through (document 202601030001). The postback does a full workflow
# render, so give it room: a false UNKNOWN is expensive here, because the
# only safe response to UNKNOWN is manual investigation.
DEFAULT_VERIFY_TIMEOUT_MS = 30000

# How long "form still on screen with 單號 = AutoNumber" must hold before it
# counts as a failed send. Reporting FAILED on first sight would misjudge a
# postback that is simply still in flight.
FAILED_CONFIRM_SECONDS = 8


@dataclass
class TripRequest:
    date: str
    start_time: str
    end_time: str
    location: str
    reason: str
    transport: str
    note: str


def _note_with_transport(trip: TripRequest) -> str:
    parts = [p for p in (trip.note, f"交通方式：{trip.transport}" if trip.transport else "") if p]
    return "；".join(parts)


def _require_frame(page):
    frame = find_trip_form_frame(page)
    if frame is None:
        raise RuntimeError("找不到出差登記表單的 frame，請先呼叫 eip_client.open_trip_form(page)。")
    return frame


def fill_form(page, trip: TripRequest) -> None:
    frame = _require_frame(page)
    frame.fill(f"#{FIELD_IDS['start_date']}", trip.date)
    frame.fill(f"#{FIELD_IDS['start_time']}", trip.start_time)
    frame.fill(f"#{FIELD_IDS['end_date']}", trip.date)
    frame.fill(f"#{FIELD_IDS['end_time']}", trip.end_time)
    frame.fill(f"#{FIELD_IDS['location']}", trip.location)
    frame.fill(f"#{FIELD_IDS['reason']}", trip.reason)
    frame.fill(f"#{FIELD_IDS['note']}", _note_with_transport(trip))


def get_filler_employee_code(page) -> str:
    """The 填單人 (form filler) employee code - always auto-filled by
    EIP itself from the logged-in session, never typed by this tool."""
    frame = _require_frame(page)
    return frame.input_value(f"#{FILLER_CODE_FIELD_ID}")


def check_required_fields(page) -> list[str]:
    """Returns a list of missing-required-field labels, empty if ok."""
    frame = _require_frame(page)
    missing = []
    for key, label in REQUIRED_FIELD_LABELS.items():
        value = frame.input_value(f"#{FIELD_IDS[key]}")
        if not value.strip():
            missing.append(label)
    return missing


class TravelerValidationError(RuntimeError):
    pass


def add_traveler(page, employee_code: str) -> str:
    """Fill the 出差人 code, let the site's own onblur validation
    (CheckPeoplePower) resolve it, then click 儲存 to add this person
    as a row in the 出差明細 grid. Returns the validated employee name.

    Raises TravelerValidationError if the code doesn't resolve to a
    real employee - the site clears both the code and name fields when
    that happens (verified by hand, see docs/eip-analysis.md section 9).
    """
    frame = _require_frame(page)
    code_locator = frame.locator(DETAIL_PERSON_CODE_SELECTOR)
    code_locator.fill(employee_code)
    code_locator.press("Tab")
    page.wait_for_timeout(1200)

    resolved_code = frame.input_value(DETAIL_PERSON_CODE_SELECTOR)
    resolved_name = frame.input_value(DETAIL_PERSON_NAME_SELECTOR)
    if not resolved_code or not resolved_name:
        raise TravelerValidationError(
            f"員工編號 {employee_code!r} 驗證失敗（欄位被清空），請確認編號是否正確。"
        )

    dialog_recorder = DialogRecorder()
    network_recorder = NetworkRecorder("儲存出差人明細")
    dialog_recorder.attach(page)
    network_recorder.attach(page)
    try:
        frame.click(DETAIL_SAVE_BUTTON_SELECTOR, timeout=8000)
        page.wait_for_timeout(1500)
    finally:
        dialog_recorder.detach()
        network_recorder.detach()
        network_recorder.save(LOG_DIR / f"save_traveler_{int(time.time())}.log")
    dialog_recorder.raise_if_unexpected()

    return resolved_name


def submit_form(page) -> None:
    """Clicks the real "傳送" (Send) button - a genuine, irreversible
    submission into the approval workflow. Only ever call this after the
    user has explicitly confirmed with `y`. Never call this during
    development/testing.

    The button's validation chain includes checkConfirmSendForm(), which
    shows a native confirm() dialog. See dialog_handler.py for the
    accept/dismiss policy - this does NOT blindly accept every dialog
    type anymore (that was flagged as a real risk in the 2026-08
    architecture review).
    """
    wrapper = find_trip_form_wrapper_frame(page)
    if wrapper is None:
        raise RuntimeError("找不到表單外層 frame（EPIE001.aspx），無法送出。")

    dialog_recorder = DialogRecorder()
    network_recorder = NetworkRecorder("傳送出差登記")
    dialog_recorder.attach(page)
    network_recorder.attach(page)
    try:
        wrapper.click(SEND_BUTTON_SELECTOR, timeout=10000)
        page.wait_for_timeout(1500)
    finally:
        dialog_recorder.detach()
        network_recorder.detach()
        network_recorder.save(LOG_DIR / f"submit_{int(time.time())}.log")
    dialog_recorder.raise_if_unexpected()


class SubmissionResult(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


def _all_frame_text(page) -> str:
    parts = []
    try:
        frames = page.frames
    except Exception:  # noqa: BLE001
        return ""
    for f in frames:
        try:
            parts.append(f.evaluate("() => document.body ? document.body.innerText : ''") or "")
        except Exception:  # noqa: BLE001 - a frame mid-navigation may not evaluate cleanly
            continue
    return "\n".join(parts)


def _submitted_document_number_from_frames(page):
    """The assigned document number, read from frame URLs. Returns None if
    no frame is showing a submitted document yet."""
    try:
        frames = page.frames
    except Exception:  # noqa: BLE001
        return None
    for f in frames:
        try:
            match = SUBMITTED_FRAME_URL_PATTERN.search(f.url)
        except Exception:  # noqa: BLE001
            continue
        if match:
            return match.group(1)
    return None


def verify_submission(page, timeout_ms: int = DEFAULT_VERIFY_TIMEOUT_MS) -> tuple[SubmissionResult, str]:
    """Call right after submit_form(). Never infer success just from the
    form view going blank/disappearing on its own - that also happens
    when the session expires mid-postback (observed for real during
    testing: a "儲存" click once led to a session-expired redirect, not
    a save, and the screen went blank exactly the same way a successful
    submission does).

    SUCCESS: either a frame URL carries SheetNo=<n>&ShowMode=ReadFormReadOnly,
    or DOCUMENT_NUMBER_PATTERN matches the rendered text. Both mean a real
    document number was assigned; the URL check is tried first because it
    becomes true earlier and does not depend on text having painted.
    FAILED: the form frame is still present and 單號 is still
    "AutoNumber" - the postback did not create a document.
    UNKNOWN: neither could be confirmed within timeout_ms (e.g. session
    expired mid-postback with no document number and no form frame
    either). Callers MUST NOT treat UNKNOWN as success, and MUST NOT
    auto-retry submit_form() on UNKNOWN - see H (duplicate protection):
    check for an existing matching submission first. Note that the
    browser's own 表單追蹤處理 list has been seen to serve a cached page
    that omitted a just-created document, so for an UNKNOWN result prefer
    an independent HTTP query of sentBox.aspx (src/http_eip_client.py).
    """
    deadline = time.time() + timeout_ms / 1000
    unchanged_since = None
    while time.time() < deadline:
        if check_session(page) == SessionState.EXPIRED:
            return (
                SubmissionResult.UNKNOWN,
                "送出過程中偵測到 session 已過期，無法確認這次送出是否成功，"
                "請重新登入後用「表單追蹤處理」查詢是否已產生單據，切勿直接重送。",
            )

        submitted_doc_no = _submitted_document_number_from_frames(page)
        if submitted_doc_no:
            return SubmissionResult.SUCCESS, f"單據編號：{submitted_doc_no}"

        text = _all_frame_text(page)
        match = DOCUMENT_NUMBER_PATTERN.search(text)
        if match:
            return SubmissionResult.SUCCESS, f"單據編號：{match.group(1)}"

        frame = find_trip_form_frame(page)
        if frame is None:
            unchanged_since = None  # form frame gone; workflow view may still be rendering
            time.sleep(0.5)
            continue

        try:
            field_doc_no = frame.input_value(f"#{DOC_NUMBER_FIELD_ID}")
        except Exception:  # noqa: BLE001
            field_doc_no = None

        if field_doc_no == "AutoNumber":
            # Do NOT conclude failure on first sight: immediately after the
            # click the old form is still on screen with 單號 unchanged
            # while the postback is in flight, so an instant verdict here
            # would report FAILED for a send that is merely slow. Require
            # the state to persist first.
            if unchanged_since is None:
                unchanged_since = time.time()
            elif time.time() - unchanged_since >= FAILED_CONFIRM_SECONDS:
                return (
                    SubmissionResult.FAILED,
                    f"表單仍在畫面上、單號仍為 AutoNumber，且持續超過 "
                    f"{FAILED_CONFIRM_SECONDS} 秒，這次送出沒有成功。",
                )
        else:
            unchanged_since = None

        time.sleep(0.5)

    return (
        SubmissionResult.UNKNOWN,
        "逾時仍無法確認送出結果，請人工檢查畫面，切勿直接重送。"
        "建議用獨立的 HTTP 查詢（src/http_eip_client.py）確認原稿資料匣，"
        "瀏覽器畫面上的清單可能是快取的舊資料。",
    )
