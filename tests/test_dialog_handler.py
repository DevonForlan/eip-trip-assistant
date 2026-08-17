import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dialog_handler import DialogRecorder, UnexpectedDialogError  # noqa: E402


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
        self.listener = None

    def on(self, event, handler):
        self.listener = handler

    def remove_listener(self, event, handler):
        self.listener = None


def test_beforeunload_is_always_accepted():
    recorder = DialogRecorder()
    page = FakePage()
    recorder.attach(page)
    dialog = FakeDialog("beforeunload", "Leave site?")
    page.listener(dialog)
    recorder.detach()

    assert dialog.accepted
    recorder.raise_if_unexpected()  # should not raise


def test_plain_confirm_is_accepted():
    recorder = DialogRecorder()
    page = FakePage()
    recorder.attach(page)
    dialog = FakeDialog("confirm", "Send this form?")
    page.listener(dialog)
    recorder.detach()

    assert dialog.accepted
    recorder.raise_if_unexpected()


def test_confirm_with_danger_keyword_is_dismissed_and_raises():
    recorder = DialogRecorder()
    page = FakePage()
    recorder.attach(page)
    dialog = FakeDialog("confirm", "此單號已存在，是否覆蓋？")
    page.listener(dialog)
    recorder.detach()

    assert dialog.dismissed
    assert not dialog.accepted
    with pytest.raises(UnexpectedDialogError):
        recorder.raise_if_unexpected()


def test_alert_is_never_auto_accepted():
    recorder = DialogRecorder()
    page = FakePage()
    recorder.attach(page)
    dialog = FakeDialog("alert", "This feature is not configured!")
    page.listener(dialog)
    recorder.detach()

    assert dialog.dismissed
    assert not dialog.accepted
    with pytest.raises(UnexpectedDialogError):
        recorder.raise_if_unexpected()


def test_prompt_is_never_auto_accepted():
    recorder = DialogRecorder()
    page = FakePage()
    recorder.attach(page)
    dialog = FakeDialog("prompt", "Enter a reason")
    page.listener(dialog)
    recorder.detach()

    with pytest.raises(UnexpectedDialogError):
        recorder.raise_if_unexpected()
