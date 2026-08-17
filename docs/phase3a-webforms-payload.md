# Phase 3A: WebForms state parser + POST payload builder

**Status: complete, with zero POSTs throughout.**

The pure-HTTP route can now reliably obtain the real 144KB ESSF21 form, parse all
153 controls (including all 63 hidden fields), and build a correct POST payload in
memory. **Nothing was sent.**

New files (none of which affect the existing Playwright/CDP route, whose files were
left completely untouched):

| File | Contents |
|---|---|
| `src/webforms_state.py` | `parse_form(html)` → `FormState`; produces the submission list per the HTML successful-controls rules. Pure stdlib, no dependency on playwright or requests |
| `src/http_eip_client.py` | `HttpEipClient`: `authenticate()` / `initialize_efnet()` / `open_trip_wrapper()` / `open_trip_form()` |
| `src/http_trip_form.py` | `build_trip_payload(form_state, trip_request)`, in-memory only |
| `scripts/http_trip_payload_dry_run.py` | Really GETs → parses → builds the payload → prints a masked diff |
| `tests/test_webforms_state.py` | 14 tests |
| `tests/test_http_trip_form.py` | 12 tests |

Tests: **66 passed** (40 before, 26 new).

## The POST guard is enforced by code, not by convention

`HttpEipClient` defaults to `_GetOnlySession`, which overrides `post` / `put` /
`patch` / `delete` to raise `ReadOnlyViolation` outright. Reaching any stage that
changes server state requires writing `HttpEipClient(read_only=False)` explicitly —
it cannot happen by slip of the hand.

---

## 1. Verification data (from a real `http_trip_payload_dry_run.py` run)

```
ASP.NET_SessionId obtained: yes
EPIE001: 97,070 bytes (full version)
ESSF21 : 144,500 bytes
form   : name="Form1" method="post"
```

### Parser results and consistency check

| Item | Parser | Raw HTML regex | |
|---|---|---|---|
| total inputs | 149 | 149 | OK |
| textarea | 4 | 4 | OK |
| select | 0 | 0 | OK |
| **hidden** | **63** | **63** | **OK** |
| text | 49 | 49 | OK |
| checkbox | 3 | 3 | OK |
| radio | 2 | 2 | OK |
| submit | 7 | 7 | OK |
| image | 25 | 25 | OK |

`total_controls = 153` (149 inputs + 4 textareas), `disabled = 12`, `unnamed = 0`,
**`successful_controls = 117`**.

That 117 reconciles: 153 − 25 image − 7 submit = 121; minus 3 unchecked checkboxes
and 1 unselected radio = 117. All 12 disabled controls are buttons, already excluded
by the type rules.

The raw HTML's `<script>` blocks contain 0 inputs, but the parser still skips script
content so that tags inside JS strings are never mistaken for controls if the page
changes in future.

---

## 2. Key findings (all of which affect future POST correctness)

### 1. `__VIEWSTATE` is empty — the real state lives in `__MSPVSTATE`

| Field | Present | Length |
|---|---|---|
| `__VIEWSTATE` | ✅ | **0** |
| `__VIEWSTATEGENERATOR` | ❌ absent | — |
| `__EVENTVALIDATION` | ❌ absent | — |
| **`__MSPVSTATE`** | ✅ | **8,164** |
| `__MSPVSTATE_ZIP` | ✅ | 4 (the value is `true`, meaning it is compressed) |
| `__TabStrip2_State__` | ✅ | 1 |

This system replaces standard ViewState with its own, compressed `__MSPVSTATE`. Any
future postback **must echo `__MSPVSTATE` back verbatim, and must never try to
generate or modify it** — it is opaque compressed data. Watching only `__VIEWSTATE`
misses the point entirely.

### 2. Three fields are `<textarea>`, not `<input>`

| Field | Tag |
|---|---|
| `ESSCCDJ024/025/026/027` (dates and times) | `<input type="text">` |
| **`ESSCCDJ028` (trip location)** | **`<textarea>`** |
| **`ESSCCDJ037` (trip reason)** | **`<textarea>`** |
| **`ESSCCDJ029` (remarks)** | **`<textarea>`** |
| `ESSCCDD005` (traveler code) | `<input type="text">` |

A textarea's value is **the text between its tags**, not a `value` attribute. A
parser that reads only `value` turns these three into empty strings silently — the
form looks submitted, but location, reason and remarks are all blank.

### 3. ⚠️ The raw HTML's checkbox state **disagrees** with the browser DOM

Section 8 of `docs/eip-analysis.md` records (from observing the DOM through
Playwright) that of those three checkboxes, "only the third is checked by default".

But **none of the three carries `checked` in the raw HTML**:

```
checkbox ESSCCDJ023$chk     checked=False
checkbox ESSCCDJ023_1$chk   checked=False
checkbox ESSCCDJ038$chk     checked=False   ← this one IS checked in the browser DOM
```

In other words, **`ESSCCDJ038_chk` is checked by JavaScript after the page loads**.

**This is the pure-HTTP route's biggest correctness risk right now**: building a
payload straight from the raw HTML submits a different checkbox state than a human
would (omitting `ESSCCDJ038$chk=on`), which could change how working hours are
computed. All three checkboxes also have hidden mirror fields (`ESSCCDJ023_hid` /
`ESSCCDJ023_1_hid` / `ESSCCDJ038_hid`, currently with no value attribute), so the
real state may be conveyed through those instead.

**This must be settled before any POST**, and the answer has to come from observing
what a real browser sends, not from guessing. It is on the capture plan below.

### 4. The save-traveler button is currently `disabled`

```html
<input type="submit" name="GridUserControl1$Button9" value="儲存"
       id="GridUserControl1_Button9" disabled="disabled" class="newbutton"
       onclick="if(!saveCheckD('createRecord')){...}
                if (!CheckDetailForm('createRecord')) {...}
                if(!SetDetailSaveButtonEnabled(this, checkRequiredFields_GridUserControl1())){...}" />

<input name="GridUserControl1$hdnBtnSaveEnabled" type="hidden"
       id="GridUserControl1_hdnBtnSaveEnabled" value="false" />
```

(The markup is quoted verbatim as the server sent it; that button's label reads
"Save".)

The button starts out disabled and is enabled by JS once validation passes, and
there is a `hdnBtnSaveEnabled` hidden field currently set to `"false"`. Per your
instruction, **no guess is made here about what state pressing it requires**, and
the payload builder deliberately adds no button field at all.

### 5. How ids and names are handled

There is no `_` → `$` string conversion. Instead, **the id is used to look up the
name the HTML actually declares**:

| logical | DOM id | actual POST name |
|---|---|---|
| start_date | `ESSCCDJ024_txt` | `ESSCCDJ024$txt` |
| location | `ESSCCDJ028_txt` | `ESSCCDJ028$txt` |
| … | … | … |

String conversion happens to work on this page, but it cannot be relied on:
`ESSCCDJ023_1_chk`'s name is `ESSCCDJ023_1$chk` (only the last underscore changes),
and an ASP.NET naming-container prefix (`ctl00$...`) would break it completely.
There is a test covering that case.

---

## 3. Payload dry-run result (masked)

```
method=post   total fields=117   distinct names=117

7 modified fields:
  ESSCCDJ024$txt  tag=<input>     old_length=0  new_length=10
  ESSCCDJ025$txt  tag=<input>     old_length=0  new_length=5
  ESSCCDJ026$txt  tag=<input>     old_length=0  new_length=10
  ESSCCDJ027$txt  tag=<input>     old_length=0  new_length=5
  ESSCCDJ028$txt  tag=<textarea>  old_length=0  new_length=8
  ESSCCDJ037$txt  tag=<textarea>  old_length=0  new_length=4
  ESSCCDJ029$txt  tag=<textarea>  old_length=0  new_length=14

preserved state:
  __VIEWSTATE       preserved=True  length=0
  __MSPVSTATE       preserved=True  length=8,164
  __MSPVSTATE_ZIP   preserved=True  length=4
  __TabStrip2_State__ preserved=True length=1

unmodified, echoed verbatim: 110 (all 63 hidden fields preserved)
GridUserControl1$Button9: absent from the payload ✅
```

The dry run uses obvious dummy data (dates like `2026/01/01`, placeholder location
and reason text) and involves no real trip information.

---

## 4. Phase 3B capture plan (proposed only, not executed)

Goal: observe the HTTP request a real browser sends when a person presses "save
traveler" (`GridUserControl1_Button9`), so it can be reconstructed rather than
guessed.

### ⚠️ Why your approval is required first

Capturing that request **necessarily means really performing one "save traveler" in
a real browser** — an action that changes server state (it adds a traveler detail
row to the draft). It is **not the same as submitting the trip application** (that
is a separate send button), but it is not read-only either. Nothing was triggered
this round, and nothing will be triggered unprompted.

### What needs capturing

| # | Item | Why |
|---|---|---|
| 1 | The POST URL (complete, Identifier masked) | Confirm whether it posts back to `ESSF21.aspx?...` itself (the form action) or to some other endpoint |
| 2 | **Which submit mechanism**: the field `GridUserControl1$Button9=儲存`, or `__doPostBack` setting `__EVENTTARGET` | The critical fork. The button is `type="submit"`, so in theory it submits as a field; but the end of the onclick chain may call `__doPostBack` instead. The two need completely different payloads, and this cannot be guessed |
| 3 | The value of `__EVENTTARGET` | If it is the postback route, the exact target string is needed |
| 4 | The value of `__EVENTARGUMENT` | Likewise |
| 5 | The complete list of POST field names | To diff against our payload's 117 names and find anything missing or extra |
| 6 | The submitted value of `GridUserControl1$hdnBtnSaveEnabled` | The HTML says `"false"`; JS presumably sets it to `"true"`. Confirm what is actually sent |
| 7 | **The actual submitted state of the three checkboxes** | Settles the discrepancy in 2.3 directly: does `ESSCCDJ038$chk` appear in a real submission's body or not |
| 8 | The submitted values of the three `_hid` mirror fields | Determines whether checkbox state travels via the checkboxes or via the hidden fields |
| 9 | The submitted length of `__MSPVSTATE` (value not recorded) | Confirm whether it is echoed verbatim or rewritten by JS before submission |
| 10 | Whether an AjaxPro XHR fires before submission | `ESSCCDD005_txt`'s onblur calls `CheckPeoplePower(pCode)`, and the earlier browser capture also showed `ajaxpro/*.ashx`. If that AJAX establishes server-side state, pure HTTP would have to reproduce it first |
| 11 | Response status | |
| 12 | Redirect chain | Whether there is a 302, and where it goes |
| 13 | Response body length, and whether it contains an error message | |
| 14 | **The new hidden state in the response** (`__MSPVSTATE`'s new length + first 8 hash chars) | Confirm the state updates after the postback, so later steps must use the new one and never reuse the old |

### Suggested approach

Add a separate passive-observation script (e.g. `scripts/capture_traveler_save.py`)
and **do not modify** `src/network_log.py` or `src/trip_form.py`. The existing
`NetworkRecorder` records field names but not values, and records neither request
headers nor the new state in responses — not enough information for the table above.

Masking follows the existing standard: `__MSPVSTATE` / `__VIEWSTATE` / Identifier /
Cookie / Authorization / personal data are recorded only as a length or the first 8
hash characters.

### An existing piece of technical debt to fix along the way

`scripts/capture_browser_sequence.py` currently reads `.content()` as soon as the
frame URL appears, without waiting for `load`/`networkidle`, so it catches truncated
mid-render HTML (previously saving 1,409 bytes instead of the real 144,494). The new
capture script should not repeat that.

---

## 5. Current status

- Phase 3A complete, all 66 tests passing
- **Zero POSTs this round**: the four new files contain no `.post(` call at all, and
  the client enforces read-only in code
- No Playwright/CDP route file was modified
- No traveler save was triggered, no draft was stored, nothing was sent, and
  `btClosejQTab` was not called
- **Phase 3B was not entered**, awaiting your instruction
