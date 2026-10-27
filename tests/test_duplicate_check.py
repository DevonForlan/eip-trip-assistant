import sys
from pathlib import Path
from types import SimpleNamespace
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import duplicate_check  # noqa: E402


class FakeGridFrame:
    def __init__(self, rows):
        self._rows = rows

    def evaluate(self, script):
        return self._rows


def make_trip(date, start_time, end_time):
    return SimpleNamespace(date=date, start_time=start_time, end_time=end_time)


REAL_ROWS = [
    {
        "docNumber": "202601020001",
        "text": "202601020001 王小明 2026/08/12 10:51:27 簽核中 未完成 王小明 2026/08/04 09:00-18:30",
    },
    {
        "docNumber": "202601010001",
        "text": "202601010001 王小明 2026/08/11 22:03:10 簽核中 未完成 王小明 2026/08/03 09:00-18:30",
    },
]


def test_finds_matching_pending_submission(monkeypatch):
    monkeypatch.setattr(
        duplicate_check, "_navigate_to_sent_originals", lambda page, timeout_ms=10000, force_reload=True: FakeGridFrame(REAL_ROWS)
    )
    trip = make_trip("2026/08/04", "09:00", "18:30")

    matches = duplicate_check.find_existing_submission(page=None, trip=trip)

    assert len(matches) == 1
    assert matches[0]["docNumber"] == "202601020001"


def test_no_match_for_unrelated_date(monkeypatch):
    monkeypatch.setattr(
        duplicate_check, "_navigate_to_sent_originals", lambda page, timeout_ms=10000, force_reload=True: FakeGridFrame(REAL_ROWS)
    )
    trip = make_trip("2026/12/25", "09:00", "18:30")

    matches = duplicate_check.find_existing_submission(page=None, trip=trip)

    assert matches == []


def test_no_match_when_time_differs_on_same_date(monkeypatch):
    monkeypatch.setattr(
        duplicate_check, "_navigate_to_sent_originals", lambda page, timeout_ms=10000, force_reload=True: FakeGridFrame(REAL_ROWS)
    )
    # same date as a real row, but a different time range - not a duplicate
    trip = make_trip("2026/08/04", "13:00", "17:00")

    matches = duplicate_check.find_existing_submission(page=None, trip=trip)

    assert matches == []


def test_empty_grid_means_no_matches(monkeypatch):
    monkeypatch.setattr(
        duplicate_check, "_navigate_to_sent_originals", lambda page, timeout_ms=10000, force_reload=True: FakeGridFrame([])
    )
    trip = make_trip("2026/08/04", "09:00", "18:30")

    assert duplicate_check.find_existing_submission(page=None, trip=trip) == []


def test_submission_timestamp_is_not_mistaken_for_the_trip_date(monkeypatch):
    """Regression from a live run: every row carries two dates - when it
    was submitted and when the trip is. Document 202601010001 was
    submitted on 2026/08/11 for a trip on 2026/08/03, and checking date /
    start / end as three separate substrings matched it for a NEW trip on
    2026/08/11, wrongly blocking a legitimate submission."""
    rows = [{
        "docNumber": "202601010001",
        "text": "202601010001 王小明 2026/08/11 22:25:11 簽核中 未完成 王小明 2026/08/03 09:00-18:30",
    }]
    monkeypatch.setattr(
        duplicate_check, "_navigate_to_sent_originals",
        lambda page, timeout_ms=10000, force_reload=True: FakeGridFrame(rows),
    )

    # The trip that was wrongly blocked.
    assert duplicate_check.find_existing_submission(
        page=None, trip=make_trip("2026/08/11", "09:00", "18:30")) == []

    # The trip that row genuinely represents must still be caught.
    assert len(duplicate_check.find_existing_submission(
        page=None, trip=make_trip("2026/08/03", "09:00", "18:30"))) == 1


def test_trip_row_pattern_tolerates_spacing_variations():
    pattern = duplicate_check.trip_row_pattern(make_trip("2026/08/04", "09:00", "18:30"))
    assert pattern.search("王小明 2026/08/04 09:00-18:30 出差登記")
    assert pattern.search("王小明 2026/08/04  09:00 - 18:30 出差登記")
    assert not pattern.search("王小明 2026/08/04 13:00-17:00 出差登記")
    assert not pattern.search("2026/08/04 10:51:27 簽核中 09:00-18:30")


def test_lookup_always_forces_a_reload(monkeypatch):
    """A cached sentBox frame once omitted a document the server already
    had, so the duplicate check must never accept a stale list."""
    seen = {}

    def fake_nav(page, timeout_ms=10000, force_reload=True):
        seen["force_reload"] = force_reload
        return FakeGridFrame(REAL_ROWS)

    monkeypatch.setattr(duplicate_check, "_navigate_to_sent_originals", fake_nav)
    duplicate_check.find_existing_submission(page=None, trip=make_trip("2026/08/04", "09:00", "18:30"))

    assert seen["force_reload"] is True


class FakeTreeFrame:
    """Mimics tree.aspx, where the tracking panel's markup is present in the
    DOM but rendered 0x0 until #tdBar4 is clicked."""

    def __init__(self, visible_after_click):
        self.visible_after_click = visible_after_click
        self.clicked = []
        self._switched = False

    def evaluate(self, script, arg=None):
        # An in-page dispatch is still a click on that button, so record it
        # the same way - these tests care that the button was activated, not
        # which mechanism did it.
        if "querySelector" in script and "el.click()" in script:
            self.clicked.append(arg)
            if arg == duplicate_check.TRACKING_BUTTON_SELECTOR:
                self._switched = True
            return True
        # The button-exists probe asks a different question from the
        # visible-text count, and answers True from the start: the markup is
        # there, it is only the panel that is hidden.
        if "querySelector" in script:
            return arg == duplicate_check.TRACKING_BUTTON_SELECTOR
        if not self._switched:
            return 0
        return 1 if arg in self.visible_after_click else 0

    def click(self, selector, timeout=None):
        self.clicked.append(selector)
        if selector == duplicate_check.TRACKING_BUTTON_SELECTOR:
            self._switched = True

    def get_by_text(self, text, exact=False):
        raise AssertionError("must not click text nodes while the panel is still hidden")


class FakePageForNav:
    def __init__(self, tree):
        self.tree = tree
        self.frames = []

    def wait_for_timeout(self, ms):
        pass


def test_hidden_tracking_panel_still_triggers_the_tdbar4_click(monkeypatch):
    """The regression that broke a live run: the panel's text exists in the
    DOM while hidden, so an existence check skipped this click entirely."""
    tree = FakeTreeFrame(visible_after_click=set())
    page = FakePageForNav(tree)
    monkeypatch.setattr(duplicate_check, "find_tree_frame", lambda p: tree)
    monkeypatch.setattr(duplicate_check, "_wait_for_visible_text",
                        lambda p, text, timeout_ms: False)

    try:
        duplicate_check._navigate_to_sent_originals(page)
    except RuntimeError:
        pass  # expected: the folder never became visible in this fake

    assert duplicate_check.TRACKING_BUTTON_SELECTOR in tree.clicked


def test_http_cross_check_returns_none_when_unavailable(monkeypatch):
    """None means 'no opinion', not 'nothing found' - callers must not
    treat an unavailable cross-check as a green light."""
    import http_eip_client

    def boom():
        raise RuntimeError("SSPI unavailable")

    monkeypatch.setattr(http_eip_client, "fetch_sent_box_rows", boom)
    assert duplicate_check.find_existing_submission_via_http(
        make_trip("2026/08/11", "09:00", "18:30")) is None


def test_http_lookup_finds_a_matching_trip(monkeypatch):
    import http_eip_client

    monkeypatch.setattr(http_eip_client, "fetch_sent_box_rows", lambda: [
        {"docNumber": "202601040001",
         "text": "202601040001 王小明 2026/08/15 16:13:44 簽核中 未完成 王小明 2026/08/06 09:00-18:30"},
    ])

    found = duplicate_check.find_existing_submission_via_http(make_trip("2026/08/06", "09:00", "18:30"))

    assert [r["docNumber"] for r in found] == ["202601040001"]


PUNCH_ROW = ("202610270060 王小明 2026/10/27 11:21:27 簽核中 未完成 王小明 2026/10/16 "
             "R24071-王大明 補刷卡申請")


def test_punch_pattern_matches_the_punch_date():
    assert duplicate_check.punch_row_pattern("2026/10/16").search(PUNCH_ROW)


def test_punch_pattern_ignores_the_submission_timestamp():
    """Filed on 10/27 for 10/16 - that is not a punch form for 10/27."""
    assert not duplicate_check.punch_row_pattern("2026/10/27").search(PUNCH_ROW)


def test_punch_pattern_ignores_trip_rows():
    trip_row = REAL_ROWS[0]["text"]
    assert not duplicate_check.punch_row_pattern("2026/08/04").search(trip_row)


def test_trip_pattern_ignores_punch_rows():
    assert not duplicate_check.trip_row_pattern(make_trip("2026/10/16", "09:00", "18:30")).search(PUNCH_ROW)


def test_wait_for_rows_returns_as_soon_as_the_row_appears(monkeypatch):
    import http_eip_client

    answers = iter([[], [], [{"docNumber": "1", "text": PUNCH_ROW}]])
    monkeypatch.setattr(http_eip_client, "fetch_sent_box_rows", lambda: next(answers))
    sleeps = []

    rows = duplicate_check.wait_for_rows_via_http(
        duplicate_check.punch_row_pattern("2026/10/16"), timeout_s=60, poll_s=5, sleep=sleeps.append)

    assert [r["docNumber"] for r in rows] == ["1"]
    assert len(sleeps) == 2


def test_wait_for_rows_distinguishes_no_answer_from_no_row(monkeypatch):
    import http_eip_client

    pattern = duplicate_check.punch_row_pattern("2026/10/16")
    monkeypatch.setattr(http_eip_client, "fetch_sent_box_rows", lambda: [])
    assert duplicate_check.wait_for_rows_via_http(pattern, timeout_s=0, sleep=lambda s: None) == []

    def boom():
        raise RuntimeError("SSPI unavailable")

    monkeypatch.setattr(http_eip_client, "fetch_sent_box_rows", boom)
    assert duplicate_check.wait_for_rows_via_http(pattern, timeout_s=0, sleep=lambda s: None) is None


def test_visible_exact_text_count_survives_a_dead_frame():
    class Boom:
        def evaluate(self, *a, **kw):
            raise RuntimeError("Frame was detached")

    assert duplicate_check._visible_exact_text_count(Boom(), "原稿資料匣") == 0


def test_navigation_waits_for_the_tracking_button_before_clicking(monkeypatch):
    """The tree frame's URL is set before its document runs, so #tdBar4 can
    genuinely not exist yet on a cold cache. Clicking straight away spent
    the 8s timeout and reported a layout change for what was a page still
    loading - it cost two live submission attempts."""

    class LateTree(FakeTreeFrame):
        def __init__(self, appears_on_probe):
            super().__init__(visible_after_click=set())
            self._appears_on_probe = appears_on_probe
            self.probes = 0

        def evaluate(self, script, arg=None):
            if "querySelector" in script and "el.click()" not in script:
                self.probes += 1
                return self.probes >= self._appears_on_probe
            return super().evaluate(script, arg)

    tree = LateTree(appears_on_probe=3)
    page = FakePageForNav(tree)
    monkeypatch.setattr(duplicate_check, "find_tree_frame", lambda p: tree)
    monkeypatch.setattr(duplicate_check, "_wait_for_visible_text",
                        lambda p, text, timeout_ms: False)

    try:
        duplicate_check._navigate_to_sent_originals(page, timeout_ms=5000)
    except RuntimeError:
        pass  # the fake never reveals the folder; the click is what matters

    assert tree.probes >= 3, "should have waited for the button to appear"
    assert duplicate_check.TRACKING_BUTTON_SELECTOR in tree.clicked


def test_navigation_reports_a_missing_tracking_button_distinctly(monkeypatch):
    class NeverAppears(FakeTreeFrame):
        def __init__(self):
            super().__init__(visible_after_click=set())

        def evaluate(self, script, arg=None):
            if "querySelector" in script:
                return False
            return super().evaluate(script, arg)

    tree = NeverAppears()
    page = FakePageForNav(tree)
    monkeypatch.setattr(duplicate_check, "find_tree_frame", lambda p: tree)

    with pytest.raises(RuntimeError) as excinfo:
        duplicate_check._navigate_to_sent_originals(page, timeout_ms=1000)

    assert "never appeared" in str(excinfo.value)
    assert duplicate_check.TRACKING_BUTTON_SELECTOR not in tree.clicked


def test_tracking_button_is_clicked_from_inside_the_page(monkeypatch):
    """Playwright's click on #tdBar4 reports the element visible, enabled and
    stable and then hangs to its timeout - seen on both the sidebar button
    and the banner shortcut. Dispatching in-page runs the same handler."""

    class Tree(FakeTreeFrame):
        def __init__(self):
            super().__init__(visible_after_click=set())
            self.in_page_clicks = []

        def evaluate(self, script, arg=None):
            if "querySelector" in script and "el.click()" in script:
                self.in_page_clicks.append(arg)
                self._switched = True
                return True
            if "querySelector" in script:
                return arg == duplicate_check.TRACKING_BUTTON_SELECTOR
            return super().evaluate(script, arg)

        def click(self, selector, timeout=None):
            raise AssertionError("should not fall back to Playwright's click here")

    tree = Tree()
    page = FakePageForNav(tree)
    monkeypatch.setattr(duplicate_check, "find_tree_frame", lambda p: tree)
    monkeypatch.setattr(duplicate_check, "_wait_for_visible_text",
                        lambda p, text, timeout_ms: False)

    try:
        duplicate_check._navigate_to_sent_originals(page, timeout_ms=5000)
    except RuntimeError:
        pass  # the fake never reveals the folder

    assert tree.in_page_clicks == [duplicate_check.TRACKING_BUTTON_SELECTOR]


def test_tracking_button_falls_back_to_a_real_click(monkeypatch):
    class Tree(FakeTreeFrame):
        def __init__(self):
            super().__init__(visible_after_click=set())

        def evaluate(self, script, arg=None):
            if "querySelector" in script and "el.click()" in script:
                return False  # in-page dispatch could not find it
            if "querySelector" in script:
                return arg == duplicate_check.TRACKING_BUTTON_SELECTOR
            return super().evaluate(script, arg)

    tree = Tree()
    page = FakePageForNav(tree)
    monkeypatch.setattr(duplicate_check, "find_tree_frame", lambda p: tree)
    monkeypatch.setattr(duplicate_check, "_wait_for_visible_text",
                        lambda p, text, timeout_ms: False)

    try:
        duplicate_check._navigate_to_sent_originals(page, timeout_ms=5000)
    except RuntimeError:
        pass

    assert duplicate_check.TRACKING_BUTTON_SELECTOR in tree.clicked
