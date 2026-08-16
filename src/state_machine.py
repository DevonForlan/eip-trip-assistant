"""Explicit state machine for the trip-submission flow.

Replaces the previous linear, implicit sequence of function calls in
main.py - there was no single place that answered "what step are we
actually on right now", which is exactly how a stale session mid-flow
turned into confusing, hard-to-diagnose failures during manual testing.

The one rule that matters most: reaching SESSION_EXPIRED is a hard,
unconditional stop. transition() itself raises SessionExpiredError when
moving into that state, so no caller can accidentally swallow it and
keep going (e.g. via a bare `except Exception` a few frames up) - the
exception has to be caught explicitly and re-authentication + a fresh
human re-confirmation must happen before the flow can restart from
AUTHENTICATED again. Nothing in this module auto-retries a send.
"""
from enum import Enum


class TripState(str, Enum):
    AUTHENTICATED = "AUTHENTICATED"
    FORM_OPEN = "FORM_OPEN"
    FORM_FILLED = "FORM_FILLED"
    TRAVELER_SAVED = "TRAVELER_SAVED"
    READY_TO_SEND = "READY_TO_SEND"
    SENDING = "SENDING"
    SENT = "SENT"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    FAILED = "FAILED"


TERMINAL_STATES = frozenset({TripState.SENT, TripState.SESSION_EXPIRED, TripState.FAILED})

# Explicit allow-list, not derived from anything - a transition that
# isn't listed here is a bug to surface loudly, not a state to silently
# tolerate. Every non-terminal state can also move to SESSION_EXPIRED or
# FAILED from anywhere, since a session can expire or an unexpected
# error can happen at any step.
_NEXT_STEPS = {
    TripState.AUTHENTICATED: {TripState.FORM_OPEN},
    TripState.FORM_OPEN: {TripState.FORM_FILLED},
    TripState.FORM_FILLED: {TripState.TRAVELER_SAVED},
    TripState.TRAVELER_SAVED: {TripState.READY_TO_SEND},
    TripState.READY_TO_SEND: {TripState.SENDING},
    TripState.SENDING: {TripState.SENT},
}
ALLOWED_TRANSITIONS = {
    state: steps | {TripState.SESSION_EXPIRED, TripState.FAILED}
    for state, steps in _NEXT_STEPS.items()
}
for _terminal in TERMINAL_STATES:
    ALLOWED_TRANSITIONS[_terminal] = set()  # terminal - nothing legally follows


class InvalidTransitionError(RuntimeError):
    pass


class SessionExpiredError(RuntimeError):
    """Raised the instant the flow transitions into SESSION_EXPIRED.

    Never intended to be caught-and-ignored. Callers must stop, surface
    this to the user, and require a fresh login + fresh confirmation
    before anything can resume.
    """


class TripFlow:
    """Tracks a single trip submission attempt from login through send.

    One instance per attempt - do not reuse across a retry after
    SESSION_EXPIRED or FAILED; start a new one once the user has
    explicitly re-confirmed they want to try again (see H: duplicate
    protection - re-confirmation must check for an existing submission
    first, never blindly resubmit).
    """

    def __init__(self):
        self.state: TripState | None = None
        self.history: list[tuple[TripState | None, TripState, str]] = []

    def transition(self, new_state: TripState, reason: str = "") -> TripState:
        if self.state is not None:
            allowed = ALLOWED_TRANSITIONS.get(self.state, set())
            if new_state not in allowed:
                raise InvalidTransitionError(
                    f"不允許的狀態轉換：{self.state.value} -> {new_state.value}"
                    f"（{reason or '無說明'}）。允許的下一步：{sorted(s.value for s in allowed)}"
                )
        self.history.append((self.state, new_state, reason))
        self.state = new_state

        if new_state is TripState.SESSION_EXPIRED:
            raise SessionExpiredError(
                f"Session 已過期（於「{reason or '未知步驟'}」偵測到），流程立即停止。"
                "禁止自動重新送出 - 請重新登入 EIP 後，重新確認一次要送出的資料再重試。"
            )
        return self.state

    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def history_summary(self) -> str:
        return " -> ".join(
            f"{(prev.value if prev else 'START')}→{new.value}"
            + (f"({reason})" if reason else "")
            for prev, new, reason in self.history
        )
