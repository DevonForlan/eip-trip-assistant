"""Fill in and submit the EIP trip-registration (ESSF21) form.

Field <-> id mapping was verified by hand in Phase 1, not guessed - see
docs/eip-analysis.md section 8. This form has NO transport-method field
(confirmed: the extra/flexible-field feature is disabled on this
tenant - its button is literally `disabled`, and its onclick only raises
an alert saying the feature is not configured), so trip.transport is
folded into the note field instead.

submit_form() clicks a real, irreversible Send button - only call it
after the user has explicitly confirmed with `y` (see src/main.py).
"""
import os
import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

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

# Traveler-detail grid - the "add a traveler" row. Verified by hand: the code
# field's own onblur calls CheckPeoplePower(code) and clears itself if
# invalid (see docs/eip-analysis.md section 9), so this fills the code
# and lets the site's own JS resolve the name, rather than guessing at
# a picker-popup flow.
DETAIL_PERSON_CODE_SELECTOR = "#ESSCCDD005_txt"
DETAIL_PERSON_NAME_SELECTOR = "#ESSCCDD006_txt"
DETAIL_SAVE_BUTTON_SELECTOR = "#GridUserControl1_Button9"

REQUIRED_FIELD_LABELS = {
    "start_date": "start date",
    "start_time": "start time",
    "end_date": "end date",
    "end_time": "end time",
    "location": "location",
    "reason": "reason",
}

# Verified by reading the button's `title` attribute (no click involved):
# MasterPage_btnCreateToolSendForm -> the real Send button.
# MasterPage_btnCreateToolSaveForm -> save-as-draft, unused here.
SEND_BUTTON_SELECTOR = "#MasterPage_btnCreateToolSendForm"

# The filer's employee code - always auto-filled by EIP from the logged-in
# user, never typed by us. Used as the default traveler (see
# get_filler_employee_code)
# since every real submission so far has the filer also be the
# traveler - a general "who else is traveling" flow is future work, not
# guessed at here.
FILLER_CODE_FIELD_ID = "ESSCCDJ004_txt"

DOC_NUMBER_FIELD_ID = "ESSCCDJ002_txt"  # document number - stays "AutoNumber" until a send succeeds

# Confirmed pattern from three successful live submissions (2026-08-11,
# 2026-08-12, 2026-08-14) - a real send replaces the form view with an
# approval workflow diagram headed by this exact text, e.g.
# "單據:ESSF21 出差登記 (202601020001)" as rendered. The number is a real, assigned
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

# How long "form still on screen with the document number = AutoNumber" must hold before it
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
        raise RuntimeError(
            "Trip-registration form frame not found - call eip_client.open_trip_form(page) first."
        )
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
    """The filer's employee code - always auto-filled by
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
    """Fill the traveler code, let the site's own onblur validation
    (CheckPeoplePower) resolve it, then click save to add this person as a
    row in the traveler-detail grid. Returns the validated employee name.

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
            f"Employee code {employee_code!r} failed validation - the site cleared the "
            "fields, which means it did not resolve to a real employee. Check the code."
        )

    dialog_recorder = DialogRecorder()
    network_recorder = NetworkRecorder("save traveler detail")
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


# The send is a heavy postback, and 10s was not enough on a cold HTTP
# cache - the click timed out mid-action, which is the one outcome that
# leaves "did it send?" genuinely unanswered.
SEND_CLICK_TIMEOUT_MS = int(os.environ.get("EIP_SEND_CLICK_TIMEOUT_MS", "45000"))


def submit_form(page) -> bool:
    """Clicks the real Send button - a genuine, irreversible
    submission into the approval workflow. Only ever call this after the
    user has explicitly confirmed with `y`. Never call this during
    development/testing.

    The button's validation chain includes checkConfirmSendForm(), which
    shows a native confirm() dialog. See dialog_handler.py for the
    accept/dismiss policy - this does NOT blindly accept every dialog
    type anymore (that was flagged as a real risk in the 2026-08
    architecture review).

    Returns True if the click timed out mid-action. That is not a failure
    signal - only verify_submission can say what actually happened - but
    callers should treat an UNKNOWN verdict after it as needing human eyes.
    """
    wrapper = find_trip_form_wrapper_frame(page)
    if wrapper is None:
        raise RuntimeError(
            "Wrapper frame (EPIE001.aspx) not found - cannot submit."
        )

    dialog_recorder = DialogRecorder()
    network_recorder = NetworkRecorder("send trip registration")
    dialog_recorder.attach(page)
    network_recorder.attach(page)
    click_timed_out = False
    try:
        try:
            wrapper.click(SEND_BUTTON_SELECTOR, timeout=SEND_CLICK_TIMEOUT_MS)
        except PlaywrightTimeoutError:
            # The click was dispatched and then timed out mid-action, which
            # says nothing about whether the submission landed. Raising here
            # skips verification and leaves exactly the ambiguity the caller
            # most needs resolved, so let verify_submission read the real
            # outcome off the page instead. This is not a retry - nothing is
            # clicked again.
            click_timed_out = True
        page.wait_for_timeout(1500)
    finally:
        dialog_recorder.detach()
        network_recorder.detach()
        network_recorder.save(LOG_DIR / f"submit_{int(time.time())}.log")
    dialog_recorder.raise_if_unexpected()
    return click_timed_out


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
    testing: a save click once led to a session-expired redirect, not
    a save, and the screen went blank exactly the same way a successful
    submission does).

    SUCCESS: either a frame URL carries SheetNo=<n>&ShowMode=ReadFormReadOnly,
    or DOCUMENT_NUMBER_PATTERN matches the rendered text. Both mean a real
    document number was assigned; the URL check is tried first because it
    becomes true earlier and does not depend on text having painted.
    FAILED: the form frame is still present and the document number is still
    "AutoNumber" - the postback did not create a document.
    UNKNOWN: neither could be confirmed within timeout_ms (e.g. session
    expired mid-postback with no document number and no form frame
    either). Callers MUST NOT treat UNKNOWN as success, and MUST NOT
    auto-retry submit_form() on UNKNOWN - see H (duplicate protection):
    check for an existing matching submission first. Note that the
    browser's own form-tracking list has been seen to serve a cached page
    that omitted a just-created document, so for an UNKNOWN result prefer
    an independent HTTP query of sentBox.aspx (src/http_eip_client.py).
    """
    deadline = time.time() + timeout_ms / 1000
    unchanged_since = None
    while time.time() < deadline:
        if check_session(page) == SessionState.EXPIRED:
            return (
                SubmissionResult.UNKNOWN,
                "The session expired mid-send, so whether it succeeded cannot be "
                "determined. Log back in and check the form-tracking drafts folder for a "
                "new document before doing anything else. Do not resend.",
            )

        submitted_doc_no = _submitted_document_number_from_frames(page)
        if submitted_doc_no:
            return SubmissionResult.SUCCESS, f"Document number: {submitted_doc_no}"

        text = _all_frame_text(page)
        match = DOCUMENT_NUMBER_PATTERN.search(text)
        if match:
            return SubmissionResult.SUCCESS, f"Document number: {match.group(1)}"

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
            # click the old form is still on screen with its document number unchanged
            # while the postback is in flight, so an instant verdict here
            # would report FAILED for a send that is merely slow. Require
            # the state to persist first.
            if unchanged_since is None:
                unchanged_since = time.time()
            elif time.time() - unchanged_since >= FAILED_CONFIRM_SECONDS:
                return (
                    SubmissionResult.FAILED,
                    "The form is still on screen with its document number still "
                    f"AutoNumber, and has been for over {FAILED_CONFIRM_SECONDS}s - "
                    "this send did not succeed.",
                )
        else:
            unchanged_since = None

        time.sleep(0.5)

    return (
        SubmissionResult.UNKNOWN,
        "Timed out without determining the outcome. Check the screen by hand and do "
        "not resend. Prefer an independent HTTP query of the drafts folder "
        "(src/http_eip_client.py) - the list shown in the browser may be cached.",
    )
