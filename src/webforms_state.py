"""Parse an ASP.NET WebForms page into its form controls and state.

Pure stdlib - deliberately imports neither playwright nor requests, so
the HTTP track can use it without dragging in the browser track and vice
versa.

Why this exists rather than "grab every DOM value": ESSF21 carries 63
hidden fields (verified against the real 144KB page - see
docs/http-essf21-access-solved.md), including non-standard ones this
system invented (`__MSPVSTATE`, `__MSPVSTATE_ZIP`, `__TabStrip2_State__`)
alongside ~30 `GridUserControl1$...` fields. Any postback has to round-trip
all of them, so the parser keeps everything it finds instead of a
hand-picked list that would silently drop state as the form evolves.

successful_controls() follows the HTML "successful controls" rules rather
than dumping every element:
  - a control needs a name to be submitted
  - disabled controls are never submitted (ESSF21 renders 12 disabled
    inputs, including the 儲存 button)
  - checkbox/radio only when checked
  - textarea submits its text content, not a value attribute
  - select submits its selected option(s)
  - submit/image/reset/button are NOT included: exactly one of them is
    submitted, and only when that specific button is the one activated,
    so the caller must add it deliberately. Nothing here guesses.
"""
from dataclasses import dataclass, field
from html.parser import HTMLParser

# Types that a plain form submission never includes on its own. submit /
# image / reset / button are added only by the act of clicking one, and
# file uploads need multipart rather than form-encoding.
EXCLUDED_INPUT_TYPES = frozenset({"submit", "image", "reset", "button", "file"})

# Fields whose presence-and-length matters when reporting, but whose
# values must never be logged (opaque, large, session-bound).
OPAQUE_STATE_FIELDS = (
    "__VIEWSTATE",
    "__VIEWSTATEGENERATOR",
    "__EVENTVALIDATION",
    "__MSPVSTATE",
    "__MSPVSTATE_ZIP",
    "__TabStrip2_State__",
)


@dataclass
class Option:
    value: str
    label: str
    selected: bool = False

    def submitted_value(self) -> str:
        """An <option> with no value attribute submits its label."""
        return self.value if self.value is not None else self.label


@dataclass
class Control:
    tag: str  # "input" | "textarea" | "select"
    name: str = ""
    id: str = ""
    type: str = ""  # lowercased input type; "" for textarea/select
    value: str = ""
    disabled: bool = False
    checked: bool = False
    multiple: bool = False
    options: list = field(default_factory=list)

    @property
    def is_hidden(self) -> bool:
        return self.tag == "input" and self.type == "hidden"

    @property
    def effective_type(self) -> str:
        """<input> with no type attribute defaults to text."""
        if self.tag != "input":
            return self.tag
        return self.type or "text"


@dataclass
class FormState:
    action: str = ""
    method: str = "get"
    name: str = ""
    id: str = ""
    controls: list = field(default_factory=list)

    def by_id(self, control_id: str):
        for c in self.controls:
            if c.id == control_id:
                return c
        return None

    def by_name(self, name: str) -> list:
        return [c for c in self.controls if c.name == name]

    def successful_controls(self) -> list:
        """(name, value) pairs a browser would submit for a plain submit,
        in document order. Deliberately excludes every button - see the
        module docstring."""
        out = []
        for c in self.controls:
            if not c.name or c.disabled:
                continue

            if c.tag == "textarea":
                out.append((c.name, c.value))
                continue

            if c.tag == "select":
                selected = [o for o in c.options if o.selected]
                # A single-select with nothing explicitly selected still
                # submits its first option, matching browser behaviour.
                if not selected and not c.multiple and c.options:
                    selected = [c.options[0]]
                for o in selected:
                    out.append((c.name, o.submitted_value()))
                continue

            t = c.effective_type
            if t in EXCLUDED_INPUT_TYPES:
                continue
            if t in ("checkbox", "radio"):
                if not c.checked:
                    continue
                # A checked box with no value attribute submits "on".
                out.append((c.name, c.value if c.value else "on"))
                continue
            out.append((c.name, c.value))
        return out

    def counts(self) -> dict:
        c = {
            "total_controls": len(self.controls),
            "hidden": 0,
            "text": 0,
            "textarea": 0,
            "checkbox": 0,
            "radio": 0,
            "submit": 0,
            "image": 0,
            "select": 0,
            "other": 0,
            "disabled": 0,
            "unnamed": 0,
        }
        for ctrl in self.controls:
            if ctrl.disabled:
                c["disabled"] += 1
            if not ctrl.name:
                c["unnamed"] += 1

            if ctrl.tag == "textarea":
                c["textarea"] += 1
            elif ctrl.tag == "select":
                c["select"] += 1
            else:
                t = ctrl.effective_type
                if t in c:
                    c[t] += 1
                else:
                    c["other"] += 1
        c["successful_controls"] = len(self.successful_controls())
        return c

    def state_field_summary(self) -> list:
        """Presence + length only for the opaque state fields - their
        values are never returned, so this is safe to log."""
        summary = []
        for name in OPAQUE_STATE_FIELDS:
            matches = self.by_name(name)
            summary.append(
                {
                    "name": name,
                    "present": bool(matches),
                    "length": len(matches[0].value) if matches else 0,
                }
            )
        return summary


class _FormParser(HTMLParser):
    """Collects controls per <form>. Content inside <script>/<style> is
    skipped so markup written by JS string literals can't register as
    phantom controls (verified: the real ESSF21 page has 0 such cases,
    but a future page change shouldn't silently corrupt the payload)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.forms = []
        self._current_form = None
        self._skip_depth = 0
        self._textarea = None
        self._select = None
        self._option = None

    @staticmethod
    def _attrs_to_dict(attrs) -> dict:
        # A bare attribute (e.g. `disabled`) arrives with value None.
        return {k.lower(): ("" if v is None else v) for k, v in attrs}

    @staticmethod
    def _has_flag(attrs_map: dict, key: str) -> bool:
        return key in attrs_map

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in ("script", "style"):
            self._skip_depth += 1
            return
        if self._skip_depth:
            return

        a = self._attrs_to_dict(attrs)

        if tag == "form":
            self._current_form = FormState(
                action=a.get("action", ""),
                method=(a.get("method", "get") or "get").lower(),
                name=a.get("name", ""),
                id=a.get("id", ""),
            )
            self.forms.append(self._current_form)
            return

        if self._current_form is None:
            return

        if tag == "input":
            self._current_form.controls.append(
                Control(
                    tag="input",
                    name=a.get("name", ""),
                    id=a.get("id", ""),
                    type=(a.get("type", "") or "").lower(),
                    value=a.get("value", ""),
                    disabled=self._has_flag(a, "disabled"),
                    checked=self._has_flag(a, "checked"),
                )
            )
        elif tag == "textarea":
            ctrl = Control(
                tag="textarea",
                name=a.get("name", ""),
                id=a.get("id", ""),
                value="",
                disabled=self._has_flag(a, "disabled"),
            )
            self._current_form.controls.append(ctrl)
            self._textarea = ctrl
        elif tag == "select":
            ctrl = Control(
                tag="select",
                name=a.get("name", ""),
                id=a.get("id", ""),
                disabled=self._has_flag(a, "disabled"),
                multiple=self._has_flag(a, "multiple"),
            )
            self._current_form.controls.append(ctrl)
            self._select = ctrl
        elif tag == "option" and self._select is not None:
            opt = Option(
                value=a.get("value") if "value" in a else None,
                label="",
                selected=self._has_flag(a, "selected"),
            )
            self._select.options.append(opt)
            self._option = opt

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ("script", "style"):
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return

        if tag == "textarea":
            self._textarea = None
        elif tag == "option":
            self._option = None
        elif tag == "select":
            self._select = None
            self._option = None
        elif tag == "form":
            self._current_form = None

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._textarea is not None:
            self._textarea.value += data
        elif self._option is not None:
            self._option.label += data


def parse_forms(html: str) -> list:
    parser = _FormParser()
    parser.feed(html)
    parser.close()
    return parser.forms


def parse_form(html: str, index: int = 0) -> FormState:
    """The form at `index` (ESSF21 has exactly one: name="Form1",
    method="post"). Raises ValueError rather than returning an empty
    FormState, so a page that changed shape fails loudly instead of
    producing a silently empty payload."""
    forms = parse_forms(html)
    if not forms:
        raise ValueError("HTML 裡找不到任何 <form>，頁面結構可能已改變。")
    if index >= len(forms):
        raise ValueError(f"HTML 只有 {len(forms)} 個 <form>，取不到第 {index} 個。")
    return forms[index]
