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


def ready_banner(name="banner"):
    """A banner whose document has actually run."""
    return FakeFrame(BANNER, name, eval_result=True)


def test_wait_for_banner_frame_tolerates_a_still_assembling_frameset():
    """A reload can leave titlebar1.aspx briefly absent; failing instantly
    reported "the page may have changed" for a page that was merely settling."""
    page = FakePage(frames_over_time=[
        [FakeFrame("http://eip/EFNET/")],
        [FakeFrame("http://eip/EFNET/")],
        [FakeFrame("http://eip/EFNET/"), ready_banner()],
    ])

    banner = eip_client.wait_for_banner_frame(page, timeout_ms=5000)

    assert banner is not None
    assert "titlebar1.aspx" in banner.url
    assert page.waits, "should have waited rather than giving up immediately"


def test_wait_for_banner_frame_gives_up_eventually():
    page = FakePage(frames=[FakeFrame("http://eip/EFNET/")])
    assert eip_client.wait_for_banner_frame(page, timeout_ms=400) is None


def test_wait_for_banner_frame_waits_for_the_document_not_just_the_url():
    """The frame's URL is set well before its document has run. Returning it
    at that point produced a click against a half-built DOM, a click that
    landed but did nothing because createTab was not defined yet, and
    td#tdMenu_1 simply missing - all from this one race."""
    not_ready = FakeFrame(BANNER, "banner", eval_result=False)
    page = FakePage(frames_over_time=[
        [not_ready],
        [not_ready],
        [ready_banner()],
    ])

    banner = eip_client.wait_for_banner_frame(page, timeout_ms=5000)

    assert banner is not None
    assert banner.evaluated, "readiness should be probed in the frame"
    assert page.waits, "should have waited for the document rather than returning early"


def test_wait_for_banner_frame_times_out_if_the_document_never_runs():
    page = FakePage(frames=[FakeFrame(BANNER, "banner", eval_result=False)])
    assert eip_client.wait_for_banner_frame(page, timeout_ms=400) is None


def test_wait_for_banner_frame_can_skip_the_readiness_check():
    page = FakePage(frames=[FakeFrame(BANNER, "banner", eval_result=False)])
    banner = eip_client.wait_for_banner_frame(page, timeout_ms=400, require_ready=False)
    assert banner is not None


def test_banner_readiness_treats_an_unevaluable_frame_as_not_ready():
    class Exploding:
        url = BANNER
        name = "banner"

        def evaluate(self, script, arg=None):
            raise RuntimeError("Execution context was destroyed")

    assert eip_client._banner_is_ready(Exploding()) is False


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


def test_open_trip_form_reuses_an_already_open_editable_form(monkeypatch):
    """A half-filled form must never be closed and rebuilt."""
    closed = []
    monkeypatch.setattr(eip_client, "close_trip_form_tab",
                        lambda page, timeout_ms=10000: closed.append(True))
    monkeypatch.setattr(eip_client, "reactivate_trip_form_tab",
                        lambda page, timeout_ms=5000: True)
    platform = FakeFrame(PLATFORM, "main", eval_result=True)
    page = FakePage(frames=[FakeFrame(BANNER, "banner"), platform, FakeFrame(TRIP_FORM, "framePlus")])

    assert eip_client.open_trip_form(page) is page
    assert closed == [], "an already-open editable form must never be closed"


def test_open_trip_form_reactivates_a_backgrounded_form(monkeypatch):
    """Regression from a live run: a previous duplicate check leaves the
    sidebar in form-tracking mode, which hides the trip-form tab. Returning
    it as-is made the caller's first fill() fail with 'element is not
    visible'."""
    reactivated = []
    monkeypatch.setattr(eip_client, "reactivate_trip_form_tab",
                        lambda page, timeout_ms=5000: reactivated.append(True) or True)
    page = FakePage(frames=[FakeFrame(PLATFORM, "main"), FakeFrame(TRIP_FORM, "framePlus")])

    eip_client.open_trip_form(page)

    assert reactivated == [True]


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
        raise AssertionError("must not close the tab when close_stale_tab=False")

    monkeypatch.setattr(eip_client, "close_trip_form_tab", fake_close)
    monkeypatch.setattr(eip_client, "wait_for_banner_frame", lambda page, timeout_ms=10000: None)
    monkeypatch.setattr(eip_client, "wait_for_platform_frame",
                        lambda page, timeout_ms=60000: object())

    page = FakePage(frames=[FakeFrame(SUBMITTED, "frameESSF21")])
    with pytest.raises(RuntimeError):
        eip_client.open_trip_form(page, close_stale_tab=False)


def test_banner_error_message_points_at_retrying_not_only_a_redesign(monkeypatch):
    monkeypatch.setattr(eip_client, "has_trip_form_tab", lambda page: False)
    monkeypatch.setattr(eip_client, "wait_for_banner_frame", lambda page, timeout_ms=10000: None)
    monkeypatch.setattr(eip_client, "wait_for_platform_frame",
                        lambda page, timeout_ms=60000: object())
    page = FakePage(frames=[])

    with pytest.raises(RuntimeError) as excinfo:
        eip_client.open_trip_form(page)

    assert "retry" in str(excinfo.value)


def test_open_trip_form_stops_early_if_platform_never_becomes_ready(monkeypatch):
    """Better a clear message about platform.aspx than waiting out the full
    timeout for a tab that was never going to be created."""
    monkeypatch.setattr(eip_client, "has_trip_form_tab", lambda page: False)
    monkeypatch.setattr(eip_client, "wait_for_platform_frame",
                        lambda page, timeout_ms=60000: None)
    page = FakePage(frames=[])

    with pytest.raises(RuntimeError) as excinfo:
        eip_client.open_trip_form(page, close_stale_tab=False)

    assert "platform.aspx" in str(excinfo.value)


class FakePlatformFrame:
    """platform.aspx, where the trip form lives in a jQuery UI tab.

    `shown_after` models how many readiness probes it takes for the panel
    to actually appear - a synthetic click that never switches the panel is
    `shown_after=None`.
    """

    url = PLATFORM
    name = "main"

    def __init__(self, shown_after=0, only_after_click=False):
        self._shown_after = shown_after
        self._only_after_click = only_after_click
        self._probes = 0
        self.evaluated = []
        self.clicks = []
        self.waits = []

    def evaluate(self, script, arg=None):
        self.evaluated.append(script)
        if "tab-ESSF21" in script:
            if self._shown_after is None:
                return False
            if self._only_after_click and not self.clicks:
                return False
            shown = self._probes >= self._shown_after
            self._probes += 1
            return shown
        return None

    def click(self, selector, timeout=None):
        self.clicks.append(selector)

    def wait_for_timeout(self, ms):
        self.waits.append(ms)


def test_reactivate_uses_an_in_page_click_and_confirms_the_panel_is_shown():
    """The tab headers are jQuery UI Tabs, so a Playwright click can register
    without switching the panel - leaving every field measuring 0x0."""
    platform = FakePlatformFrame(shown_after=0)
    page = FakePage(frames=[FakeFrame("http://eip/EFNET/"), platform])

    assert eip_client.reactivate_trip_form_tab(page) is True
    assert any("getElementById('ESSF21')" in s for s in platform.evaluated)
    assert platform.clicks == [], "the in-page click should have sufficed"


def test_reactivate_falls_back_to_a_real_click_then_rechecks():
    """If the in-page click does not switch the panel, the Playwright click
    still gets a turn - and its result is verified too, not assumed."""
    platform = FakePlatformFrame(only_after_click=True)
    page = FakePage(frames=[FakeFrame("http://eip/EFNET/"), platform])

    assert eip_client.reactivate_trip_form_tab(page, timeout_ms=600) is True
    assert platform.clicks == [eip_client.TRIP_FORM_TAB_ANCHOR_SELECTOR]


def test_reactivate_reports_failure_when_the_panel_never_appears():
    """"The click did not raise" is not the same as "the tab switched", and
    treating it as such is what let a hidden form reach fill()."""
    platform = FakePlatformFrame(shown_after=None)
    page = FakePage(frames=[FakeFrame("http://eip/EFNET/"), platform])

    assert eip_client.reactivate_trip_form_tab(page, timeout_ms=600) is False


def test_reactivate_without_a_platform_frame_is_false_not_an_error():
    page = FakePage(frames=[FakeFrame("http://eip/EFNET/")])
    assert eip_client.reactivate_trip_form_tab(page) is False


def test_wait_for_platform_frame_waits_for_the_tabs_widget():
    """createTab() adds the form's tab to the widget in platform.aspx. Run
    before that frame is ready it does nothing at all - no error, no tab -
    and the caller then waits out its whole timeout for a form frame that
    was never coming."""
    not_ready = FakeFrame(PLATFORM, "main", eval_result=False)
    ready = FakeFrame(PLATFORM, "main", eval_result=True)
    page = FakePage(frames_over_time=[[not_ready], [not_ready], [ready]])

    frame = eip_client.wait_for_platform_frame(page, timeout_ms=5000)

    assert frame is not None
    assert page.waits, "should have waited for the widget"


def test_wait_for_platform_frame_times_out_when_it_never_loads():
    page = FakePage(frames=[FakeFrame(PLATFORM, "main", eval_result=False)])
    assert eip_client.wait_for_platform_frame(page, timeout_ms=400) is None


def test_wait_for_platform_frame_without_the_frame_at_all():
    page = FakePage(frames=[FakeFrame("http://eip/EFNET/")])
    assert eip_client.wait_for_platform_frame(page, timeout_ms=400) is None
