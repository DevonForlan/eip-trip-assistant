import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import eip_client  # noqa: E402


class FakeFrame:
    def __init__(self, url, name="", eval_result=None):
        self.url = url
        self.name = name
        self._eval_result = eval_result
        self.evaluated = []

    def evaluate(self, script, arg=None):
        self.evaluated.append((script, arg))
        if callable(self._eval_result):
            return self._eval_result(script, arg)
        return self._eval_result


class FakePage:
    """Frames can be produced lazily so a test can model a frameset that is
    still assembling."""

    def __init__(self, frames=(), frames_over_time=None):
        self._frames = list(frames)
        self._frames_over_time = list(frames_over_time or [])
        self.waits = []

    @property
    def frames(self):
        if self._frames_over_time:
            self._frames = self._frames_over_time.pop(0)
        return self._frames

    def wait_for_timeout(self, ms):
        self.waits.append(ms)


BANNER = "http://eip/EFNET/src/_Common/AppUtil/FrameSet/titlebar1.aspx"
PLATFORM = "http://eip/EFNET/src/_Common/AppUtil/FrameSet/platform.aspx"
TRIP_FORM = "http://eip/HRMESS/src/ESS/ESSF21/ESSF21.aspx?Identifier=abc"
SUBMITTED = "http://eip/EFNET/src/_Common/AppUtil/FlowChart/FlowChart.aspx?SheetNo=1&ShowMode=ReadFormReadOnly"


def test_wait_for_banner_frame_tolerates_a_still_assembling_frameset():
    """A reload can leave titlebar1.aspx briefly absent; failing instantly
    reported '畫面可能已改版' for a page that was merely settling."""
    page = FakePage(frames_over_time=[
        [FakeFrame("http://eip/EFNET/")],
        [FakeFrame("http://eip/EFNET/")],
        [FakeFrame("http://eip/EFNET/"), FakeFrame(BANNER, "banner")],
    ])

    banner = eip_client.wait_for_banner_frame(page, timeout_ms=5000)

    assert banner is not None
    assert "titlebar1.aspx" in banner.url
    assert page.waits, "should have waited rather than giving up immediately"


def test_wait_for_banner_frame_gives_up_eventually():
    page = FakePage(frames=[FakeFrame("http://eip/EFNET/")])
    assert eip_client.wait_for_banner_frame(page, timeout_ms=400) is None


def test_has_trip_form_tab_true_when_platform_reports_the_anchor():
    page = FakePage(frames=[FakeFrame(PLATFORM, "main", eval_result=True)])
    assert eip_client.has_trip_form_tab(page) is True


def test_has_trip_form_tab_false_without_a_platform_frame():
    page = FakePage(frames=[FakeFrame(BANNER, "banner")])
    assert eip_client.has_trip_form_tab(page) is False


def test_close_trip_form_tab_reports_success_once_the_tab_is_gone():
    calls = {"n": 0}

    def evaluator(script, arg):
        calls["n"] += 1
        if "closer.click()" in script:
            return True
        return calls["n"] < 3  # tab still reported present for one poll

    page = FakePage(frames=[FakeFrame(PLATFORM, "main", eval_result=evaluator)])

    assert eip_client.close_trip_form_tab(page, timeout_ms=5000) is True


def test_close_trip_form_tab_false_when_there_is_no_close_icon():
    page = FakePage(frames=[FakeFrame(PLATFORM, "main", eval_result=False)])
    assert eip_client.close_trip_form_tab(page, timeout_ms=500) is False


def test_open_trip_form_reuses_an_already_open_editable_form():
    """A half-filled form must never be closed and rebuilt."""
    platform = FakeFrame(PLATFORM, "main", eval_result=True)
    page = FakePage(frames=[FakeFrame(BANNER, "banner"), platform, FakeFrame(TRIP_FORM, "framePlus")])

    assert eip_client.open_trip_form(page) is page
    assert platform.evaluated == [], "must not even look at the tab, let alone close it"


def test_open_trip_form_closes_a_spent_tab_before_clicking(monkeypatch):
    """After a send the tab holds a read-only document, so the shortcut
    would just re-activate it and no new form would ever load."""
    closed = {"called": False}
    monkeypatch.setattr(eip_client, "has_trip_form_tab", lambda page: True)

    def fake_close(page, timeout_ms=10000):
        closed["called"] = True
        return True

    monkeypatch.setattr(eip_client, "close_trip_form_tab", fake_close)
    monkeypatch.setattr(eip_client, "wait_for_banner_frame", lambda page, timeout_ms=10000: None)

    page = FakePage(frames=[FakeFrame(SUBMITTED, "frameESSF21")])
    with pytest.raises(RuntimeError):
        eip_client.open_trip_form(page)

    assert closed["called"] is True


def test_open_trip_form_can_opt_out_of_closing(monkeypatch):
    monkeypatch.setattr(eip_client, "has_trip_form_tab", lambda page: True)

    def fake_close(page, timeout_ms=10000):
        raise AssertionError("close_stale_tab=False 時不應該關閉分頁籤")

    monkeypatch.setattr(eip_client, "close_trip_form_tab", fake_close)
    monkeypatch.setattr(eip_client, "wait_for_banner_frame", lambda page, timeout_ms=10000: None)

    page = FakePage(frames=[FakeFrame(SUBMITTED, "frameESSF21")])
    with pytest.raises(RuntimeError):
        eip_client.open_trip_form(page, close_stale_tab=False)


def test_banner_error_message_points_at_retrying_not_only_a_redesign(monkeypatch):
    monkeypatch.setattr(eip_client, "has_trip_form_tab", lambda page: False)
    monkeypatch.setattr(eip_client, "wait_for_banner_frame", lambda page, timeout_ms=10000: None)
    page = FakePage(frames=[])

    with pytest.raises(RuntimeError) as excinfo:
        eip_client.open_trip_form(page)

    assert "重試" in str(excinfo.value)
