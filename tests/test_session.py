"""Tests for session state detection."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from session import SessionState, check_session, wait_until_authenticated  # noqa: E402

HOME_FRAMES = [
    "http://eip.example.com/EFNET/",
    "http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/titlebar1.aspx",
    "http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/tree.aspx",
    "http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/platform.aspx",
]


class FakeFrame:
    def __init__(self, url):
        self.url = url


class FakePage:
    def __init__(self, url, frame_urls=(), body_text="", frames_over_time=None):
        self.url = url
        self.frames = [FakeFrame(u) for u in frame_urls]
        self._body_text = body_text
        self._frames_over_time = list(frames_over_time or [])
        self.waits = []

    def evaluate(self, script):
        return self._body_text

    def wait_for_timeout(self, ms):
        self.waits.append(ms)
        if self._frames_over_time:
            self.frames = [FakeFrame(u) for u in self._frames_over_time.pop(0)]


def test_authenticated_homepage():
    page = FakePage(
        url="http://eip.example.com/EFNET/",
        frame_urls=[
            "http://eip.example.com/EFNET/",
            "http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/titlebar1.aspx",
            "http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/tree.aspx",
            "http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/platform.aspx",
        ],
    )
    assert check_session(page) == SessionState.AUTHENTICATED


def test_expired_via_logout_url():
    page = FakePage(
        url="http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/ChromeADLogout.htm?Lang=Lang01"
    )
    assert check_session(page) == SessionState.EXPIRED


def test_expired_via_logout_frame():
    page = FakePage(
        url="http://eip.example.com/EFNET/",
        frame_urls=[
            "http://eip.example.com/EFNET/",
            "http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/ChromeADLogout.htm",
        ],
    )
    assert check_session(page) == SessionState.EXPIRED


def test_expired_via_page_text():
    page = FakePage(
        url="http://eip.example.com/EFNET/",
        body_text="Session過期，敬請重新登入",
    )
    assert check_session(page) == SessionState.EXPIRED


def test_unknown_when_shape_unrecognized():
    page = FakePage(url="http://eip.example.com/EFNET/", frame_urls=["about:blank"])
    assert check_session(page) == SessionState.UNKNOWN


def test_wait_until_authenticated_lets_a_settling_frameset_finish():
    """A frameset still assembling reads as UNKNOWN; judging instantly
    aborted runs over sessions that were about to be fine."""
    page = FakePage(
        url="http://eip.example.com/EFNET/",
        frame_urls=["about:blank"],
        frames_over_time=[["about:blank"], HOME_FRAMES],
    )

    assert wait_until_authenticated(page, timeout_ms=5000) == SessionState.AUTHENTICATED
    assert page.waits, "should have waited instead of deciding immediately"


def test_wait_until_authenticated_returns_expired_without_waiting():
    """EXPIRED will not improve with time, and callers must stop on it."""
    page = FakePage(
        url="http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/ChromeADLogout.htm"
    )

    assert wait_until_authenticated(page, timeout_ms=5000) == SessionState.EXPIRED
    assert page.waits == []


def test_wait_until_authenticated_gives_up_and_reports_unknown():
    page = FakePage(url="http://eip.example.com/EFNET/", frame_urls=["about:blank"])
    assert wait_until_authenticated(page, timeout_ms=400) == SessionState.UNKNOWN


def test_wait_until_authenticated_returns_immediately_when_already_good():
    page = FakePage(url="http://eip.example.com/EFNET/", frame_urls=HOME_FRAMES)
    assert wait_until_authenticated(page) == SessionState.AUTHENTICATED
    assert page.waits == []
