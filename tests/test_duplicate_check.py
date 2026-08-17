import sys
from pathlib import Path
from types import SimpleNamespace

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
        if not self._switched:
            return 0
        return 1 if arg in self.visible_after_click else 0

    def click(self, selector, timeout=None):
        self.clicked.append(selector)
        if selector == duplicate_check.TRACKING_BUTTON_SELECTOR:
            self._switched = True

    def get_by_text(self, text, exact=False):
        raise AssertionError("不應該在面板尚未顯示時就去點文字節點")


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


def test_visible_exact_text_count_survives_a_dead_frame():
    class Boom:
        def evaluate(self, *a, **kw):
            raise RuntimeError("Frame was detached")

    assert duplicate_check._visible_exact_text_count(Boom(), "原稿資料匣") == 0
