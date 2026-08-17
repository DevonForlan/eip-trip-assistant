import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import trip_form  # noqa: E402
from dialog_handler import UnexpectedDialogError  # noqa: E402
from session import SessionState  # noqa: E402
from trip_form import (  # noqa: E402
    DETAIL_PERSON_CODE_SELECTOR,
    DETAIL_PERSON_NAME_SELECTOR,
    DETAIL_SAVE_BUTTON_SELECTOR,
    DOC_NUMBER_FIELD_ID,
    FIELD_IDS,
    SubmissionResult,
    TravelerValidationError,
    TripRequest,
    _note_with_transport,
)


@pytest.fixture(autouse=True)
def _isolate_log_dir(monkeypatch, tmp_path):
    """add_traveler()/submit_form() write a network log file after every
    call - redirect that to a pytest tmp dir so tests never write into
    the real project's logs/ directory."""
    monkeypatch.setattr(trip_form, "LOG_DIR", tmp_path)


class FakeLocator:
    def __init__(self, frame, selector):
        self.frame = frame
        self.selector = selector

    def fill(self, value):
        self.frame.filled[self.selector] = value
        if self.selector == DETAIL_PERSON_CODE_SELECTOR and value in self.frame.known_employees:
            self.frame.filled[DETAIL_PERSON_NAME_SELECTOR] = self.frame.known_employees[value]

    def press(self, key):
        pass


class FakeFrame:
    def __init__(self):
        self.filled = {}
        self.clicked = []
        self.known_employees = {}  # code -> name, simulates onblur validation
        self.on_click = {}  # selector -> callback, simulates a dialog firing

    def fill(self, selector, value):
        self.filled[selector] = value

    def input_value(self, selector):
        return self.filled.get(selector, "")

    def click(self, selector, timeout=None):
        self.clicked.append(selector)
        if selector in self.on_click:
            self.on_click[selector]()

    def locator(self, selector):
        return FakeLocator(self, selector)


class FakeDialog:
    def __init__(self, dialog_type, message):
        self.type = dialog_type
        self.message = message
        self.accepted = False
        self.dismissed = False

    def accept(self):
        self.accepted = True

    def dismiss(self):
        self.dismissed = True


class FakePage:
    def __init__(self):
        self.listeners = {}

    def on(self, event, handler):
        self.listeners[event] = handler

    def remove_listener(self, event, handler):
        self.listeners.pop(event, None)

    def wait_for_timeout(self, ms):
        pass

    def fire_dialog(self, dialog_type, message):
        dialog = FakeDialog(dialog_type, message)
        self.listeners["dialog"](dialog)
        return dialog


def make_trip(**overrides):
    defaults = dict(
        date="2026/08/12",
        start_time="09:00",
        end_time="17:30",
        location="Client site A",
        reason="Database maintenance",
        transport="MRT",
        note="quarterly maintenance",
    )
    defaults.update(overrides)
    return TripRequest(**defaults)


def test_trip_request_holds_fields():
    trip = make_trip()
    assert trip.date == "2026/08/12"
    assert trip.location == "Client site A"


def test_note_with_transport_appends_transport():
    trip = make_trip(note="note text", transport="MRT")
    combined = _note_with_transport(trip)
    assert "note text" in combined
    assert "交通方式：MRT" in combined


def test_note_with_transport_handles_empty_transport():
    trip = make_trip(note="note text", transport="")
    assert _note_with_transport(trip) == "note text"


def test_get_filler_employee_code_reads_autofilled_field(monkeypatch):
    fake_frame = FakeFrame()
    fake_frame.filled[f"#{trip_form.FILLER_CODE_FIELD_ID}"] = "E12345"
    monkeypatch.setattr(trip_form, "find_trip_form_frame", lambda page: fake_frame)

    assert trip_form.get_filler_employee_code(page=None) == "E12345"


def test_fill_form_writes_expected_fields(monkeypatch):
    fake_frame = FakeFrame()
    monkeypatch.setattr(trip_form, "find_trip_form_frame", lambda page: fake_frame)

    trip_form.fill_form(page=None, trip=make_trip())

    assert fake_frame.filled[f"#{FIELD_IDS['location']}"] == "Client site A"
    assert fake_frame.filled[f"#{FIELD_IDS['start_date']}"] == "2026/08/12"
    assert fake_frame.filled[f"#{FIELD_IDS['end_date']}"] == "2026/08/12"
    assert "交通方式：MRT" in fake_frame.filled[f"#{FIELD_IDS['note']}"]


def test_check_required_fields_reports_missing(monkeypatch):
    fake_frame = FakeFrame()
    fake_frame.filled[f"#{FIELD_IDS['start_date']}"] = "2026/08/12"
    monkeypatch.setattr(trip_form, "find_trip_form_frame", lambda page: fake_frame)

    missing = trip_form.check_required_fields(page=None)

    assert "start time" in missing
    assert "start date" not in missing


def test_submit_form_clicks_send_button(monkeypatch):
    fake_frame = FakeFrame()
    fake_page = FakePage()
    monkeypatch.setattr(trip_form, "find_trip_form_wrapper_frame", lambda page: fake_frame)

    trip_form.submit_form(page=fake_page)

    assert trip_form.SEND_BUTTON_SELECTOR in fake_frame.clicked
    assert "dialog" not in fake_page.listeners  # cleaned up after click


def test_submit_form_accepts_plain_confirm(monkeypatch):
    fake_frame = FakeFrame()
    fake_page = FakePage()
    monkeypatch.setattr(trip_form, "find_trip_form_wrapper_frame", lambda page: fake_frame)
    dialogs = []
    fake_frame.on_click[trip_form.SEND_BUTTON_SELECTOR] = lambda: dialogs.append(
        fake_page.fire_dialog("confirm", "Send this form?")
    )

    trip_form.submit_form(page=fake_page)  # should not raise

    assert dialogs[0].accepted


def test_submit_form_raises_on_unexpected_alert(monkeypatch):
    fake_frame = FakeFrame()
    fake_page = FakePage()
    monkeypatch.setattr(trip_form, "find_trip_form_wrapper_frame", lambda page: fake_frame)
    fake_frame.on_click[trip_form.SEND_BUTTON_SELECTOR] = lambda: fake_page.fire_dialog(
        "alert", "unexpected error"
    )

    with pytest.raises(UnexpectedDialogError):
        trip_form.submit_form(page=fake_page)


def test_submit_form_raises_on_danger_keyword_confirm(monkeypatch):
    fake_frame = FakeFrame()
    fake_page = FakePage()
    monkeypatch.setattr(trip_form, "find_trip_form_wrapper_frame", lambda page: fake_frame)
    fake_frame.on_click[trip_form.SEND_BUTTON_SELECTOR] = lambda: fake_page.fire_dialog(
        "confirm", "此單號已存在，是否覆蓋？"
    )

    with pytest.raises(UnexpectedDialogError):
        trip_form.submit_form(page=fake_page)


def test_add_traveler_success(monkeypatch):
    fake_frame = FakeFrame()
    fake_frame.known_employees["E12345"] = "Test Employee"
    fake_page = FakePage()
    monkeypatch.setattr(trip_form, "find_trip_form_frame", lambda page: fake_frame)

    name = trip_form.add_traveler(page=fake_page, employee_code="E12345")

    assert name == "Test Employee"
    assert fake_frame.filled[DETAIL_PERSON_CODE_SELECTOR] == "E12345"
    assert DETAIL_SAVE_BUTTON_SELECTOR in fake_frame.clicked


def test_add_traveler_invalid_code_raises(monkeypatch):
    fake_frame = FakeFrame()  # no known_employees - code won't resolve
    fake_page = FakePage()
    monkeypatch.setattr(trip_form, "find_trip_form_frame", lambda page: fake_frame)

    with pytest.raises(TravelerValidationError):
        trip_form.add_traveler(page=fake_page, employee_code="R99999")

    assert DETAIL_SAVE_BUTTON_SELECTOR not in fake_frame.clicked  # never got that far


class FakeVerifyFrame:
    """A frame for verify_submission tests: .evaluate() returns whatever
    text was configured for it, standing in for document.body.innerText.
    `url` matters too now that a submitted document is also detected from
    frame URLs.
    """

    def __init__(self, text="", url=""):
        self.text = text
        self.url = url

    def evaluate(self, script):
        return self.text


class FakeVerifyPage:
    def __init__(self, frame_texts=(), frame_urls=()):
        urls = list(frame_urls) + [""] * (len(frame_texts) - len(frame_urls))
        self.frames = [FakeVerifyFrame(t, u) for t, u in zip(frame_texts, urls)]


def test_verify_submission_success_on_document_number(monkeypatch):
    monkeypatch.setattr(trip_form, "check_session", lambda page: SessionState.AUTHENTICATED)
    page = FakeVerifyPage(frame_texts=["填表人\n單據:ESSF21 出差登記 (202601020001)\n第 1 關"])

    result, detail = trip_form.verify_submission(page)

    assert result == SubmissionResult.SUCCESS
    assert "202601020001" in detail


def test_verify_submission_success_from_frame_url(monkeypatch):
    """The signal that a real send actually produced: the form frame is
    replaced by FlowChart.aspx carrying SheetNo + ReadFormReadOnly. This
    became true before the text had painted, which is why a genuinely
    successful send (202601030001) was reported UNKNOWN before."""
    monkeypatch.setattr(trip_form, "check_session", lambda page: SessionState.AUTHENTICATED)
    page = FakeVerifyPage(
        frame_texts=["", ""],
        frame_urls=[
            "http://eip/EFNET/src/_Common/AppUtil/FrameSet/tree.aspx",
            "http://eip/EFNET/src/_Common/AppUtil/FlowChart/FlowChart.aspx"
            "?FormID=ESSF21&SheetNo=202601030001&ShowMode=ReadFormReadOnly",
        ],
    )

    result, detail = trip_form.verify_submission(page)

    assert result == SubmissionResult.SUCCESS
    assert "202601030001" in detail


def test_verify_submission_failed_when_autonumber_persists(monkeypatch):
    monkeypatch.setattr(trip_form, "check_session", lambda page: SessionState.AUTHENTICATED)
    monkeypatch.setattr(trip_form, "FAILED_CONFIRM_SECONDS", 0.1)
    fake_frame = FakeFrame()
    fake_frame.filled[f"#{DOC_NUMBER_FIELD_ID}"] = "AutoNumber"
    monkeypatch.setattr(trip_form, "find_trip_form_frame", lambda page: fake_frame)
    page = FakeVerifyPage(frame_texts=["the form is still on screen"])

    result, detail = trip_form.verify_submission(page, timeout_ms=3000)

    assert result == SubmissionResult.FAILED
    assert "AutoNumber" in detail


def test_verify_submission_does_not_call_failure_on_first_sight(monkeypatch):
    """A postback still in flight leaves the old form on screen with its
    document number unchanged; concluding FAILED immediately would
    misreport it."""
    monkeypatch.setattr(trip_form, "check_session", lambda page: SessionState.AUTHENTICATED)
    monkeypatch.setattr(trip_form, "FAILED_CONFIRM_SECONDS", 60)
    fake_frame = FakeFrame()
    fake_frame.filled[f"#{DOC_NUMBER_FIELD_ID}"] = "AutoNumber"
    monkeypatch.setattr(trip_form, "find_trip_form_frame", lambda page: fake_frame)
    page = FakeVerifyPage(frame_texts=["the form is still on screen"])

    result, _ = trip_form.verify_submission(page, timeout_ms=600)

    assert result == SubmissionResult.UNKNOWN  # not FAILED


def test_verify_submission_unknown_when_session_expired_mid_postback(monkeypatch):
    monkeypatch.setattr(trip_form, "check_session", lambda page: SessionState.EXPIRED)
    page = FakeVerifyPage(frame_texts=["Session過期，敬請重新登入"])

    result, detail = trip_form.verify_submission(page, timeout_ms=100)

    assert result == SubmissionResult.UNKNOWN
    assert "resend" in detail  # must warn against blindly retrying


def test_verify_submission_unknown_on_timeout_with_no_signal(monkeypatch):
    monkeypatch.setattr(trip_form, "check_session", lambda page: SessionState.AUTHENTICATED)
    monkeypatch.setattr(trip_form, "find_trip_form_frame", lambda page: None)
    page = FakeVerifyPage(frame_texts=["some intermediate screen"])

    result, detail = trip_form.verify_submission(page, timeout_ms=100)

    assert result == SubmissionResult.UNKNOWN
