"""Build an ESSF21 POST payload in memory from a parsed form + trip data.

Nothing here sends anything. It produces the body a submission *would*
carry, so it can be inspected before any decision to POST is made.

DOM id vs POST name: the page uses `ESSCCDJ024_txt` as the element id but
`ESSCCDJ024$txt` as the submitted name (ASP.NET naming containers). Rather
than string-swapping `_` for `$` - which would be a guess, and wrong for
ids that legitimately contain underscores (`ESSCCDJ023_1_chk` submits as
`ESSCCDJ023_1$chk`) - this module looks each field up by id in the parsed
form and uses whatever `name` the HTML actually declares.

Field shapes were verified against the real 144KB page, not assumed:
  ESSCCDJ024/025/026/027 are <input type="text">
  ESSCCDJ028 (地點), ESSCCDJ037 (事由), ESSCCDJ029 (備註) are <textarea>
  ESSCCDD005 (出差人代號) is <input type="text">
A textarea's value is its text content, which is why the parser tracks
that separately - reading a `value` attribute here would silently yield
empty strings.

Deliberately absent: any button field. ESSF21's 儲存 button renders as
`<input type="submit" name="GridUserControl1$Button9" disabled="disabled">`
with a client-side validation chain and a companion
`GridUserControl1$hdnBtnSaveEnabled` hidden field currently set to
"false". What that button actually requires on the wire has not been
observed yet, so nothing here fabricates it.
"""
from dataclasses import dataclass, field

# logical name -> DOM id. The POST name is resolved from the parsed HTML.
TRIP_FIELD_DOM_IDS = {
    "start_date": "ESSCCDJ024_txt",
    "start_time": "ESSCCDJ025_txt",
    "end_date": "ESSCCDJ026_txt",
    "end_time": "ESSCCDJ027_txt",
    "location": "ESSCCDJ028_txt",
    "reason": "ESSCCDJ037_txt",
    "note": "ESSCCDJ029_txt",
}

TRAVELER_CODE_DOM_ID = "ESSCCDD005_txt"


class PayloadBuildError(RuntimeError):
    pass


@dataclass
class FieldChange:
    logical: str
    dom_id: str
    post_name: str
    tag: str
    is_hidden: bool
    old_present: bool
    old_length: int
    new_length: int


@dataclass
class TripPayload:
    action_url: str
    method: str
    fields: list = field(default_factory=list)  # list[(name, value)], order preserved
    changes: list = field(default_factory=list)

    def field_names(self) -> list:
        return [n for n, _ in self.fields]

    def value_length(self, name: str):
        for n, v in self.fields:
            if n == name:
                return len(v)
        return None

    def summary(self) -> dict:
        return {
            "action_url": self.action_url,
            "method": self.method,
            "field_count": len(self.fields),
            "distinct_names": len(set(self.field_names())),
            "changed_field_count": len(self.changes),
        }


def note_with_transport(note: str, transport: str) -> str:
    """ESSF21 has no transport field (the 彈性欄位 feature is disabled on
    this tenant), so transport is folded into 備註.

    Mirrors trip_form._note_with_transport in the Playwright track. The
    two are intentionally separate - importing that module here would drag
    playwright into the HTTP track - but they must be changed together,
    or the same trip would file differently depending on which track ran.
    """
    parts = [p for p in (note, f"交通方式：{transport}" if transport else "") if p]
    return "；".join(parts)


def _resolve(form_state, dom_id: str, logical: str):
    control = form_state.by_id(dom_id)
    if control is None:
        raise PayloadBuildError(
            f"表單裡找不到欄位 {logical}（id={dom_id}）。"
            "頁面可能已改版，請重新確認欄位對照表，不要繼續建立 payload。"
        )
    if not control.name:
        raise PayloadBuildError(f"欄位 {logical}（id={dom_id}）沒有 name，無法送出。")
    if control.disabled:
        raise PayloadBuildError(
            f"欄位 {logical}（id={dom_id}）是 disabled，瀏覽器不會送出它，"
            "強行加入會產生與真實操作不同的請求。"
        )
    return control


def _override(fields: list, name: str, new_value: str) -> bool:
    for i, (n, _v) in enumerate(fields):
        if n == name:
            fields[i] = (name, new_value)
            return True
    return False


def build_trip_payload(form_state, trip_request, action_url: str = None,
                       traveler_code: str = None) -> TripPayload:
    """Overlay `trip_request` onto the form's existing successful controls.

    `trip_request` is duck-typed - anything with .date, .start_time,
    .end_time, .location, .reason, .transport and .note works (e.g.
    trip_form.TripRequest), so the HTTP track needs no import from the
    Playwright track.

    Every hidden field the server sent is carried through untouched: the
    payload starts as the form's own successful controls and only the trip
    fields are replaced.
    """
    values = {
        "start_date": trip_request.date,
        "start_time": trip_request.start_time,
        # Single-day trip: end date mirrors start date, matching the
        # Playwright track's fill_form().
        "end_date": trip_request.date,
        "end_time": trip_request.end_time,
        "location": trip_request.location,
        "reason": trip_request.reason,
        "note": note_with_transport(
            getattr(trip_request, "note", "") or "",
            getattr(trip_request, "transport", "") or "",
        ),
    }

    fields = list(form_state.successful_controls())
    changes = []

    targets = dict(TRIP_FIELD_DOM_IDS)
    if traveler_code is not None:
        targets["traveler_code"] = TRAVELER_CODE_DOM_ID
        values["traveler_code"] = traveler_code

    for logical, dom_id in targets.items():
        control = _resolve(form_state, dom_id, logical)
        new_value = values[logical]
        if not _override(fields, control.name, new_value):
            raise PayloadBuildError(
                f"欄位 {logical}（name={control.name}）不在表單會送出的控制項清單中，"
                "代表它被判定為不可送出，payload 會缺少這筆資料。"
            )
        changes.append(
            FieldChange(
                logical=logical,
                dom_id=dom_id,
                post_name=control.name,
                tag=control.tag,
                is_hidden=control.is_hidden,
                old_present=bool(control.value),
                old_length=len(control.value),
                new_length=len(new_value),
            )
        )

    resolved_action = action_url if action_url is not None else form_state.action
    return TripPayload(
        action_url=resolved_action,
        method=(form_state.method or "post").lower(),
        fields=fields,
        changes=changes,
    )
