import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import webforms_state  # noqa: E402
from webforms_state import parse_form  # noqa: E402


def test_parses_form_attributes_and_keeps_every_hidden_field():
    form = parse_form(
        '<html><body><form name="Form1" method="post" action="X.aspx?a=1">'
        '<input type="hidden" name="__MSPVSTATE" value="abc" />'
        '<input type="hidden" name="__MSPVSTATE_ZIP" value="true" />'
        '<input type="text" name="t$txt" id="t_txt" value="" />'
        "</form></body></html>"
    )
    assert form.name == "Form1"
    assert form.method == "post"
    # entities in attributes are unescaped by the parser
    assert form.action == "X.aspx?a=1"
    assert form.counts()["hidden"] == 2
    names = [n for n, _ in form.successful_controls()]
    assert names == ["__MSPVSTATE", "__MSPVSTATE_ZIP", "t$txt"]


def test_disabled_and_button_controls_are_not_submitted():
    """ESSF21 renders 12 disabled inputs (including the save button) and
    32 submit/image buttons - none may end up in a payload."""
    form = parse_form(
        "<form>"
        '<input type="text" name="ok" value="1" />'
        '<input type="text" name="off" value="2" disabled="disabled" />'
        '<input type="submit" name="btnSave" value="Save" />'
        '<input type="image" name="btnImg" />'
        '<input type="reset" name="btnReset" />'
        '<input type="button" name="btnPlain" />'
        "</form>"
    )
    assert [n for n, _ in form.successful_controls()] == ["ok"]


def test_unnamed_control_is_not_submitted():
    form = parse_form('<form><input type="text" value="x" /></form>')
    assert form.successful_controls() == []
    assert form.counts()["unnamed"] == 1


def test_checkbox_only_when_checked_and_defaults_to_on():
    form = parse_form(
        "<form>"
        '<input type="checkbox" name="a" />'
        '<input type="checkbox" name="b" checked="checked" />'
        '<input type="checkbox" name="c" value="Y" checked />'
        "</form>"
    )
    assert form.successful_controls() == [("b", "on"), ("c", "Y")]


def test_radio_group_submits_only_the_checked_option():
    form = parse_form(
        "<form>"
        '<input type="radio" name="r" value="1" />'
        '<input type="radio" name="r" value="2" checked="checked" />'
        "</form>"
    )
    assert form.successful_controls() == [("r", "2")]


def test_textarea_submits_its_text_content_not_a_value_attribute():
    """Location / reason / note are textareas - reading a value attribute here
    would silently submit empty strings."""
    form = parse_form('<form><textarea name="note$txt" id="note_txt">existing text</textarea></form>')
    ctrl = form.by_id("note_txt")
    assert ctrl.tag == "textarea"
    assert ctrl.value == "existing text"
    assert form.successful_controls() == [("note$txt", "existing text")]


def test_select_submits_selected_option_and_falls_back_to_first():
    form = parse_form(
        "<form>"
        '<select name="s1"><option value="a">A</option>'
        '<option value="b" selected="selected">B</option></select>'
        '<select name="s2"><option value="x">X</option><option value="y">Y</option></select>'
        "</form>"
    )
    assert form.successful_controls() == [("s1", "b"), ("s2", "x")]


def test_option_without_value_submits_its_label():
    form = parse_form('<form><select name="s"><option selected>Label</option></select></form>')
    assert form.successful_controls() == [("s", "Label")]


def test_controls_written_inside_script_are_ignored():
    """A future page change that emits markup from JS must not inject
    phantom controls into the payload."""
    form = parse_form(
        "<form>"
        '<input type="text" name="real" value="1" />'
        '<script>document.write(\'<input type="hidden" name="fake" value="9">\');</script>'
        "</form>"
    )
    assert [n for n, _ in form.successful_controls()] == ["real"]
    assert form.by_name("fake") == []


def test_by_id_and_by_name_lookups():
    form = parse_form(
        "<form>"
        '<input type="text" name="dup" value="1" />'
        '<input type="text" name="dup" value="2" id="second" />'
        "</form>"
    )
    assert len(form.by_name("dup")) == 2
    assert form.by_id("second").value == "2"
    assert form.by_id("missing") is None


def test_state_field_summary_reports_presence_and_length_only():
    form = parse_form(
        '<form><input type="hidden" name="__MSPVSTATE" value="1234567890" /></form>'
    )
    summary = {s["name"]: s for s in form.state_field_summary()}
    assert summary["__MSPVSTATE"]["present"] is True
    assert summary["__MSPVSTATE"]["length"] == 10
    assert summary["__EVENTVALIDATION"]["present"] is False
    # the raw value must never leak into the summary
    assert all("value" not in s for s in form.state_field_summary())


def test_input_without_type_defaults_to_text():
    form = parse_form('<form><input name="n" value="v" /></form>')
    assert form.controls[0].effective_type == "text"
    assert form.successful_controls() == [("n", "v")]


def test_missing_form_raises_rather_than_returning_empty():
    with pytest.raises(ValueError):
        parse_form("<html><body>no form here</body></html>")


def test_excluded_types_constant_covers_every_button_kind():
    assert webforms_state.EXCLUDED_INPUT_TYPES >= {"submit", "image", "reset", "button", "file"}
