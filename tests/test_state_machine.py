import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from state_machine import (  # noqa: E402
    InvalidTransitionError,
    SessionExpiredError,
    TripFlow,
    TripState,
)


def test_happy_path_transitions_in_order():
    flow = TripFlow()
    flow.transition(TripState.AUTHENTICATED, "login")
    flow.transition(TripState.FORM_OPEN, "open form")
    flow.transition(TripState.FORM_FILLED, "fill header")
    flow.transition(TripState.TRAVELER_SAVED, "save traveler")
    flow.transition(TripState.READY_TO_SEND, "final confirm")
    flow.transition(TripState.SENDING, "click send")
    flow.transition(TripState.SENT, "verified")

    assert flow.state == TripState.SENT
    assert flow.is_terminal()


def test_skipping_a_step_is_rejected():
    flow = TripFlow()
    flow.transition(TripState.AUTHENTICATED, "login")
    with pytest.raises(InvalidTransitionError):
        flow.transition(TripState.READY_TO_SEND, "skip ahead")


def test_session_expired_raises_and_halts():
    flow = TripFlow()
    flow.transition(TripState.AUTHENTICATED, "login")
    flow.transition(TripState.FORM_OPEN, "open form")

    with pytest.raises(SessionExpiredError):
        flow.transition(TripState.SESSION_EXPIRED, "check_session before save")

    assert flow.state == TripState.SESSION_EXPIRED
    assert flow.is_terminal()


def test_terminal_state_accepts_no_further_transitions():
    flow = TripFlow()
    flow.transition(TripState.AUTHENTICATED, "login")
    flow.transition(TripState.FORM_OPEN, "open form")
    flow.transition(TripState.FORM_FILLED, "fill header")
    flow.transition(TripState.TRAVELER_SAVED, "save traveler")
    flow.transition(TripState.READY_TO_SEND, "final confirm")
    flow.transition(TripState.SENDING, "click send")
    flow.transition(TripState.SENT, "verified")

    with pytest.raises(InvalidTransitionError):
        flow.transition(TripState.SENDING, "accidental resend")


def test_any_non_terminal_state_can_fail():
    flow = TripFlow()
    flow.transition(TripState.AUTHENTICATED, "login")
    flow.transition(TripState.FORM_OPEN, "open form")
    flow.transition(TripState.FAILED, "unexpected error")
    assert flow.state == TripState.FAILED
    assert flow.is_terminal()
