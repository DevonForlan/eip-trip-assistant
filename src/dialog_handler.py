"""Classifies and handles Playwright dialogs during a single action.

Fixes the previous behaviour in trip_form.submit_form(), which
registered a listener that called dialog.accept() unconditionally for
*any* dialog type - a real risk flagged in the 2026-08 architecture
review: an unexpected confirm() (e.g. "this document number already
exists, overwrite?") would have been clicked through without anyone
noticing.

Policy:
- beforeunload: always accept. We just triggered this navigation
  ourselves (clicking Save/Send causes a postback), so "leave this
  page?" is expected and safe to answer yes to.
- confirm: accept only if the message doesn't contain a "danger"
  keyword. Every confirm() seen in this flow (checkConfirmSendForm())
  is expected to be a plain "proceed?" prompt - none has been observed
  with genuinely dangerous wording, but the message is unconfirmed
  verbatim (a live capture attempt hit a session/connection issue
  before the text could be read - see docs/eip-analysis.md). Until a
  known-good message is captured and hardcoded as an explicit
  allowlist, this keyword blocklist is the safety net: anything
  mentioning duplicates/errors/overwrite gets dismissed and raised
  instead of blindly clicked through.
- alert / prompt: never auto-accept. Nothing in the known EIP flows is
  expected to raise these during a normal save/send - if one appears,
  something unexpected is happening and a human needs to look.
"""
from dataclasses import dataclass, field

# Substrings that, if found in a confirm() message, mean "do not accept
# automatically" regardless of dialog type. Case-sensitive on purpose -
# these are specific Chinese terms expected to appear verbatim in EIP's
# own JS-generated messages, not user input we need to normalize.
DANGER_KEYWORDS = (
    "已存在",
    "重複",
    "覆蓋",
    "錯誤",
    "失敗",
    "逾時",
    "過期",
)


@dataclass
class DialogEvent:
    dialog_type: str
    message: str
    action: str  # "accepted" | "dismissed"


class UnexpectedDialogError(RuntimeError):
    def __init__(self, dialog_type: str, message: str):
        self.dialog_type = dialog_type
        self.message = message
        super().__init__(
            f"跳出未預期的 {dialog_type} 對話框，訊息：「{message}」。"
            "已自動 dismiss（不接受），避免誤送/誤存 - 請人工確認畫面狀態後再重試。"
        )


@dataclass
class DialogRecorder:
    """Attach for the duration of one action via attach(page), then
    call detach() and raise_if_unexpected() afterward - deliberately
    NOT raising from inside the dialog callback itself, since an
    exception raised there may not reliably propagate back through
    Playwright's sync-API event dispatch to the calling code.
    """

    events: list = field(default_factory=list)
    unexpected: DialogEvent | None = None
    _page: object = field(default=None, repr=False)

    def _handle(self, dialog) -> None:
        dialog_type = dialog.type
        message = dialog.message

        if dialog_type == "beforeunload":
            dialog.accept()
            action = "accepted"
        elif dialog_type == "confirm" and not any(k in message for k in DANGER_KEYWORDS):
            dialog.accept()
            action = "accepted"
        else:
            dialog.dismiss()
            action = "dismissed"

        event = DialogEvent(dialog_type, message, action)
        self.events.append(event)
        if action == "dismissed":
            self.unexpected = event

    def attach(self, page) -> "DialogRecorder":
        self._page = page
        page.on("dialog", self._handle)
        return self

    def detach(self) -> None:
        if self._page is not None:
            self._page.remove_listener("dialog", self._handle)
            self._page = None

    def raise_if_unexpected(self) -> None:
        if self.unexpected is not None:
            raise UnexpectedDialogError(self.unexpected.dialog_type, self.unexpected.message)
