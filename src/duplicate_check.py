"""Duplicate-submission protection (H in the 2026-08 architecture review).

If submit_form() fails or trip_form.verify_submission() returns UNKNOWN,
nothing may retry the send blindly - that risks filing the same trip
twice. Before any retry (or before a fresh send that a user asked to
redo after an earlier ambiguous result), check the form-tracking
drafts folder for a pending ESSF21 submission that already matches this
trip's date, time and traveler.

DOM verified by hand against two real submissions
(202601020001, 202601010001) - not guessed:
- #tdBar4 (in the tree.aspx frame) switches the sidebar into
  form-tracking mode.
- Its drafts > uncategorized node loads a frame at
  .../FormBox/sentBox.aspx?FolderID=... containing a standard ASP.NET
  GridView (id="GridView1").
- Each result row's document-number cell has a `title` attribute equal
  to the document number itself (e.g. title="202601020001") - this is
  what this module keys off of, rather than a specific row CSS class
  name, since only the title-attribute pattern was directly confirmed.
- The subject column reads "{filer name} {date} {start}-{end}", e.g.
  "王小明 2026/08/04 09:00-18:30" - confirmed from both real
  submissions, and what matching is based on here.

2026-08-14: two real bugs found while using this against a live form, both
fixed below.

1. Visibility vs existence. The tracking sidebar (FormBoxTree /
   divFormBox1 / divInbox) is always present in tree.aspx's DOM but
   rendered 0x0 until #tdBar4 is clicked. The old code decided "already in
   tracking mode" with `get_by_text(...).count() > 0`, which is satisfied by
   that hidden markup - so it skipped clicking #tdBar4 entirely and then
   timed out waiting for a folder that was never shown. Everything here now
   tests whether an element is actually rendered.

2. exact=False matched the wrong node. Matching the folder label with
   exact=False also matches the large hidden container divs (their
   combined text contains that string) and `.first` picked one of those.
   Matching is exact=True now, so only the leaf node qualifies.

Known remaining limitation: the browser can keep serving a previously
loaded sentBox frame rather than re-querying, so this can report a stale
list. That happened during a real submission - a document created seconds
earlier was absent here while the server already had it. So
find_existing_submission() forces a reload, and callers must understand
that "no match" from the browser view is weaker evidence than an
independent HTTP GET of sentBox.aspx (src/http_eip_client.py), which was
authoritative in that incident.
"""
import re
import time

from eip_client import find_tree_frame

TRACKING_BUTTON_SELECTOR = "#tdBar4"
ORIGINAL_FOLDER_TEXT = "原稿資料匣"
UNCATEGORIZED_FOLDER_TEXT = "未分類"
SENT_BOX_FRAME_FRAGMENT = "FormBox/sentBox.aspx"

# Clicking #tdBar4 swaps sidebar panels via script; the old 1s wait was not
# enough in practice, and the symptom was a confusing timeout further down.
PANEL_SWITCH_TIMEOUT_MS = 15000


def _visible_exact_text_count(frame, text: str) -> int:
    """How many rendered elements have exactly this trimmed text.

    Measured with getBoundingClientRect in the page rather than via a
    Playwright visibility check, because the bug being fixed here was
    picking up hidden container elements in the first place - the scoping
    has to be unambiguous, not just the visibility test.
    """
    try:
        return frame.evaluate(
            """(t) => {
                let n = 0;
                for (const el of document.querySelectorAll('a, span, td')) {
                    if ((el.textContent || '').trim() === t) {
                        const r = el.getBoundingClientRect();
                        if (r.width && r.height) n++;
                    }
                }
                return n;
            }""",
            text,
        )
    except Exception:  # noqa: BLE001 - a frame mid-navigation may not evaluate
        return 0


def _wait_for_visible_text(page, text: str, timeout_ms: int) -> bool:
    """Poll until `text` is actually rendered in the (re-fetched) tree frame."""
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        tree = find_tree_frame(page)
        if tree is not None and _visible_exact_text_count(tree, text) > 0:
            return True
        page.wait_for_timeout(300)
    return False


def _find_sent_box_frame(page):
    for f in page.frames:
        if SENT_BOX_FRAME_FRAGMENT in f.url:
            return f
    return None


def _click_if_visible(locator, timeout=3000) -> bool:
    """Best-effort click - the sidebar tree's expand/collapse state
    carries over between calls (it's not reset just by us looking at
    it), so a folder that's already expanded from a previous run may
    already show its child, or clicking it again may collapse it
    instead. Rather than assume a fixed sequence of clicks always
    applies, each step here only clicks if there's something visible
    to click, and the frame-appearing check below is what actually
    decides whether navigation succeeded."""
    try:
        if locator.count() == 0:
            return False
        first = locator.first
        if not first.is_visible():
            return False
        first.click(timeout=timeout)
        return True
    except Exception:  # noqa: BLE001
        return False


def _navigate_to_sent_originals(page, timeout_ms: int = 10000, force_reload: bool = True):
    """Get the drafts > uncategorized grid frame, clicking through the
    sidebar as needed.

    force_reload re-clicks the folder even when a sentBox frame is already
    present. Returning the existing frame is faster but can hand back a
    list the browser cached earlier - which is exactly how a freshly
    created document went missing during a real submission.
    """
    if not force_reload:
        existing = _find_sent_box_frame(page)
        if existing is not None:
            return existing

    tree = find_tree_frame(page)
    if tree is None:
        raise RuntimeError(
            "Sidebar tree frame (tree.aspx) not found - cannot query form tracking."
        )

    # #tdBar4 shows the tracking panel. Test for the folder being RENDERED,
    # not merely present: the panel's markup exists (0x0) from page load, so
    # an existence check here silently skips this click - see module docstring.
    if _visible_exact_text_count(tree, ORIGINAL_FOLDER_TEXT) == 0:
        try:
            tree.click(TRACKING_BUTTON_SELECTOR, timeout=8000)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                f"Failed to click the form-tracking button ({TRACKING_BUTTON_SELECTOR}): {e}"
            ) from e
        if not _wait_for_visible_text(page, ORIGINAL_FOLDER_TEXT, PANEL_SWITCH_TIMEOUT_MS):
            raise RuntimeError(
                "Clicked the form-tracking button but the drafts folder never became "
                "visible - the sidebar structure may have changed."
            )

    # Expand the drafts folder so its uncategorized child appears.
    tree = find_tree_frame(page)
    if _visible_exact_text_count(tree, UNCATEGORIZED_FOLDER_TEXT) == 0:
        _click_if_visible(tree.get_by_text(ORIGINAL_FOLDER_TEXT, exact=True))
        _wait_for_visible_text(page, UNCATEGORIZED_FOLDER_TEXT, PANEL_SWITCH_TIMEOUT_MS)

    tree = find_tree_frame(page)
    if _visible_exact_text_count(tree, UNCATEGORIZED_FOLDER_TEXT) == 0:
        raise RuntimeError(
            "The drafts folder is visible but expanding it revealed no uncategorized "
            "node - the sidebar structure may have changed."
        )
    _click_if_visible(tree.get_by_text(UNCATEGORIZED_FOLDER_TEXT, exact=True))

    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        frame = _find_sent_box_frame(page)
        if frame is not None:
            try:
                frame.wait_for_load_state("networkidle", timeout=8000)
            except Exception:  # noqa: BLE001 - best effort; grid may already be idle
                pass
            return frame
        page.wait_for_timeout(300)

    raise RuntimeError(
        "Clicked through form tracking > drafts > uncategorized but the draft list "
        "never finished loading - the page may have changed, or the tree is in an "
        "unexpected expand/collapse state."
    )


def _extract_document_rows(grid_frame) -> list:
    """Every row whose first cell with a `title` attribute looks like a
    document number (digits only, 6+ long) - deliberately not keyed off
    a specific row CSS class name, since only the title-attribute
    pattern was directly confirmed against real data."""
    return grid_frame.evaluate(
        """() => {
        const grid = document.getElementById('GridView1');
        if (!grid) return [];
        const rows = Array.from(grid.querySelectorAll('tr'));
        const out = [];
        for (const tr of rows) {
            const cell = tr.querySelector('td[title]');
            if (!cell) continue;
            const title = (cell.getAttribute('title') || '').trim();
            if (/^\\d{6,}$/.test(title)) {
                out.push({
                    docNumber: title,
                    text: (tr.innerText || '').replace(/\\t/g, ' ').trim(),
                });
            }
        }
        return out;
    }"""
    )


def trip_row_pattern(trip) -> "re.Pattern":
    """Matches the subject column's "{trip date} {start}-{end}" run.

    Deliberately one contiguous pattern rather than three independent
    substring checks. A row carries TWO dates - when it was submitted and
    when the trip is - e.g.

        202601010001 王小明 2026/08/11 22:25:11 簽核中 未完成 王小明 2026/08/03 09:00-18:30

    Checking date/start/end separately matched that row for a trip on
    2026/08/11, because the submission timestamp happened to carry that
    date while the times came from the unrelated 08/03 trip. That false
    positive blocked a legitimate submission. Requiring the date to be
    immediately followed by the time range keeps the two columns apart.
    """
    return re.compile(
        re.escape(trip.date) + r"\s+" + re.escape(trip.start_time)
        + r"\s*-\s*" + re.escape(trip.end_time)
    )


def find_existing_submission(page, trip, timeout_ms: int = 10000) -> list:
    """Returns a list of {docNumber, text} for open ESSF21 submissions
    whose subject shows this exact trip date and time range - i.e. a
    likely duplicate of `trip`. Empty list means no match found under the
    folder's default "not yet closed" filter.

    `trip` needs .date, .start_time, .end_time attributes (a
    trip_form.TripRequest works directly).

    An empty result is good evidence but not proof: the browser's sentBox
    frame has been observed serving a cached list that omitted a document
    the server already had. This forces a reload to reduce that risk, and
    anything that must be certain (e.g. confirming an ambiguous send
    actually landed) should query sentBox.aspx over HTTP instead.
    """
    grid_frame = _navigate_to_sent_originals(page, timeout_ms=timeout_ms, force_reload=True)
    rows = _extract_document_rows(grid_frame)

    pattern = trip_row_pattern(trip)
    return [row for row in rows if pattern.search(row.get("text", ""))]


def find_existing_submission_via_http(trip):
    """The same lookup over plain HTTP, bypassing the browser entirely.

    Returns the matching rows, or None if the HTTP route could not answer -
    None means "no opinion", NOT "nothing found", and callers must not read
    it as a green light.

    Exists because the browser's list is not authoritative: it has been
    observed omitting a document the server already had, and a missed
    duplicate means filing the same trip twice. Imported lazily so the
    Playwright track does not pull in requests/SSPI just by importing this
    module.
    """
    try:
        from http_eip_client import fetch_sent_box_rows
        rows = fetch_sent_box_rows()
    except Exception:  # noqa: BLE001 - an unavailable cross-check must not block
        return None

    pattern = trip_row_pattern(trip)
    return [row for row in rows if pattern.search(row.get("text", ""))]


def find_existing_submission_anywhere(page, trip, timeout_ms: int = 10000) -> list:
    """Union of the browser view and the HTTP view, de-duplicated by
    document number.

    Either source reporting a match is enough to stop: the cost of a false
    positive is re-checking by hand, while the cost of a false negative is
    a duplicate application in the approval workflow.
    """
    matches = {row["docNumber"]: row for row in
               find_existing_submission(page, trip, timeout_ms=timeout_ms)}

    http_matches = find_existing_submission_via_http(trip)
    if http_matches is not None:
        for row in http_matches:
            matches.setdefault(row["docNumber"], row)
    return list(matches.values())
