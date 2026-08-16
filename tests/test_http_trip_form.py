import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import http_trip_form  # noqa: E402
from http_trip_form import PayloadBuildError, build_trip_payload, note_with_transport  # noqa: E402
from webforms_state import parse_form  # noqa: E402


@dataclass
class FakeTrip:
    date: str = "2026/08/05"
    start_time: str = "09:00"
    end_time: str = "18:30"
    location: str = "客戶端 A 辦公室"
    reason: str = "系統建置"
    transport: str = "捷運"
    note: str = "備註"


def _form_html(extra: str = "") -> str:
    """A miniature ESSF21 mirroring the real page's shapes: text inputs for
    dates/times, textareas for location/reason/note, plus hidden state."""
    return (
        '<form name="Form1" method="post" action="ESSF21.aspx?Identifier=abc">'
        '<input type="hidden" name="__MSPVSTATE" value="STATE" />'
        '<input type="hidden" name="__MSPVSTATE_ZIP" value="true" />'
        '<input type="hidden" name="__VIEWSTATE" value="" />'
        '<input type="text" name="ESSCCDJ024$txt" id="ESSCCDJ024_txt" value="" />'
        '<input type="text" name="ESSCCDJ025$txt" id="ESSCCDJ025_txt" value="" />'
        '<input type="text" name="ESSCCDJ026$txt" id="ESSCCDJ026_txt" value="" />'
        '<input type="text" name="ESSCCDJ027$txt" id="ESSCCDJ027_txt" value="" />'
        '<textarea name="ESSCCDJ028$txt" id="ESSCCDJ028_txt"></textarea>'
        '<textarea name="ESSCCDJ037$txt" id="ESSCCDJ037_txt"></textarea>'
        '<textarea name="ESSCCDJ029$txt" id="ESSCCDJ029_txt"></textarea>'
        '<input type="text" name="ESSCCDD005$txt" id="ESSCCDD005_txt" value="" />'
        '<input type="submit" name="GridUserControl1$Button9" value="儲存" disabled="disabled" />'
        + extra
        + "</form>"
    )


def test_trip_fields_land_on_the_names_declared_in_the_html():
    form = parse_form(_form_html())
    payload = build_trip_payload(form, FakeTrip())
    values = dict(payload.fields)
    assert values["ESSCCDJ024$txt"] == "2026/08/05"
    assert values["ESSCCDJ025$txt"] == "09:00"
    assert values["ESSCCDJ026$txt"] == "2026/08/05"  # single-day trip mirrors start
    assert values["ESSCCDJ027$txt"] == "18:30"
    assert values["ESSCCDJ028$txt"] == "客戶端 A 辦公室"
    assert values["ESSCCDJ037$txt"] == "系統建置"


def test_post_name_is_read_from_html_not_derived_from_the_id():
    """The id->name relationship is a naming-container artifact, not a rule
    we may reproduce by string surgery. If the HTML declares something
    unexpected, the payload must follow the HTML."""
    html = _form_html().replace(
        '<input type="text" name="ESSCCDJ024$txt" id="ESSCCDJ024_txt" value="" />',
        '<input type="text" name="ctl00$X$ESSCCDJ024$txt" id="ESSCCDJ024_txt" value="" />',
    )
    payload = build_trip_payload(parse_form(html), FakeTrip())
    names = payload.field_names()
    assert "ctl00$X$ESSCCDJ024$txt" in names
    assert "ESSCCDJ024$txt" not in names


def test_every_hidden_state_field_is_carried_through_untouched():
    form = parse_form(_form_html())
    payload = build_trip_payload(form, FakeTrip())
    values = dict(payload.fields)
    assert values["__MSPVSTATE"] == "STATE"
    assert values["__MSPVSTATE_ZIP"] == "true"
    assert values["__VIEWSTATE"] == ""
    changed = {c.post_name for c in payload.changes}
    assert "__MSPVSTATE" not in changed


def test_disabled_save_button_never_enters_the_payload():
    form = parse_form(_form_html())
    payload = build_trip_payload(form, FakeTrip())
    assert "GridUserControl1$Button9" not in payload.field_names()


def test_transport_is_folded_into_the_note_field():
    form = parse_form(_form_html())
    payload = build_trip_payload(form, FakeTrip())
    assert dict(payload.fields)["ESSCCDJ029$txt"] == "備註；交通方式：捷運"


def test_note_with_transport_handles_empty_parts():
    assert note_with_transport("", "") == ""
    assert note_with_transport("只有備註", "") == "只有備註"
    assert note_with_transport("", "捷運") == "交通方式：捷運"


def test_traveler_code_is_only_included_when_asked_for():
    form = parse_form(_form_html())
    without = build_trip_payload(form, FakeTrip())
    assert dict(without.fields)["ESSCCDD005$txt"] == ""

    with_code = build_trip_payload(parse_form(_form_html()), FakeTrip(), traveler_code="E12345")
    assert dict(with_code.fields)["ESSCCDD005$txt"] == "E12345"


def test_missing_field_raises_instead_of_silently_dropping_data():
    html = _form_html().replace(
        '<textarea name="ESSCCDJ028$txt" id="ESSCCDJ028_txt"></textarea>', ""
    )
    with pytest.raises(PayloadBuildError):
        build_trip_payload(parse_form(html), FakeTrip())


def test_disabled_target_field_raises():
    html = _form_html().replace(
        '<input type="text" name="ESSCCDJ024$txt" id="ESSCCDJ024_txt" value="" />',
        '<input type="text" name="ESSCCDJ024$txt" id="ESSCCDJ024_txt" value="" disabled />',
    )
    with pytest.raises(PayloadBuildError):
        build_trip_payload(parse_form(html), FakeTrip())


def test_changes_record_lengths_only_for_safe_logging():
    form = parse_form(_form_html())
    payload = build_trip_payload(form, FakeTrip())
    change = next(c for c in payload.changes if c.logical == "start_date")
    assert change.old_length == 0
    assert change.new_length == len("2026/08/05")
    assert change.tag == "input"
    assert not hasattr(change, "new_value")


def test_action_url_override_wins_over_form_action():
    form = parse_form(_form_html())
    payload = build_trip_payload(form, FakeTrip(), action_url="http://host/abs.aspx")
    assert payload.action_url == "http://host/abs.aspx"
    assert payload.method == "post"


def test_field_mapping_covers_all_seven_trip_fields():
    assert set(http_trip_form.TRIP_FIELD_DOM_IDS) == {
        "start_date", "start_time", "end_date", "end_time", "location", "reason", "note",
    }
