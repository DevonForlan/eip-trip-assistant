import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import punch_form  # noqa: E402
from punch_form import PunchRequest, PunchValidationError  # noqa: E402


def good_readback(req):
    actual = dict(punch_form.expected_values(req))
    actual[punch_form.REASON_ID_FIELD_ID] = "0001"
    return actual


def test_valid_request_passes():
    PunchRequest("2026/10/16", ["08:30"]).validate()
    PunchRequest("2026/10/23", ["08:30", "18:00"], "其他", "10/23(五)颱風日居家辦公補打卡").validate()


@pytest.mark.parametrize("req", [
    PunchRequest("2026-10-16", ["08:30"]),
    PunchRequest("2026/10/16", []),
    PunchRequest("2026/10/16", ["8:30"]),
    PunchRequest("2026/10/16", ["24:00"]),
    PunchRequest("2026/10/16", ["08:30"] * 7),
    PunchRequest("2026/10/16", ["08:30"], "颱風"),
])
def test_invalid_request_is_rejected(req):
    with pytest.raises(PunchValidationError):
        req.validate()


def test_unused_time_slots_are_expected_empty():
    expected = punch_form.expected_values(PunchRequest("2026/10/16", ["08:30", "18:00"]))
    assert [expected[f] for f in punch_form.TIME_FIELD_IDS] == ["08:30", "18:00", "", "", "", ""]
    assert all(expected[f] == "2026/10/16" for f in punch_form.DATE_FIELD_IDS)


def test_matching_readback_has_no_mismatches():
    req = PunchRequest("2026/10/16", ["08:30"])
    assert punch_form.mismatches(req, good_readback(req)) == {}


def test_leftover_time_is_a_mismatch():
    req = PunchRequest("2026/10/16", ["08:30"])
    actual = good_readback(req)
    actual[punch_form.TIME_FIELD_IDS[1]] = "18:00"
    assert punch_form.TIME_FIELD_IDS[1] in punch_form.mismatches(req, actual)


def test_reason_name_without_its_id_is_a_mismatch():
    """Typed text can show the right name while the coded id the server
    checks is empty - exactly how a typed reason fails."""
    req = PunchRequest("2026/10/16", ["08:30"])
    actual = good_readback(req)
    actual[punch_form.REASON_ID_FIELD_ID] = ""
    assert punch_form.REASON_ID_FIELD_ID in punch_form.mismatches(req, actual)
