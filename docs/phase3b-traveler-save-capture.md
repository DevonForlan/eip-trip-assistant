# Phase 3B: browser ground truth for saving a traveler

**Status: complete. The save succeeded (`hdnGridDataCount` 0 → 1), the button was
pressed exactly once, and the trip application was not submitted.**

Script: `scripts/capture_traveler_save.py` (one-shot, with guards).
Raw data: `logs/traveler_save_capture/` (gitignored).

**The three most important findings all overturned the working assumptions:**

1. **The submit mechanism is neither A nor B** but a third thing: a 0-pixel hidden
   `<input type="image">` named `BtnDetailSave`, submitting the coordinates
   `BtnDetailSave.x` / `BtnDetailSave.y`. `__EVENTTARGET` is **empty**, and
   `GridUserControl1$Button9` is **absent from the POST body entirely**.
2. **`CheckPeoplePower`'s AJAX writes server-side session state** (it does not merely
   query), so a pure-HTTP replay has to reproduce it first.
3. **A pre-click DOM snapshot cannot predict the POST contents** — the onclick handler
   chain mutates state again before submitting.

---

## 1. The four-way diff

| Field | 1. Raw HTML | 2. Browser DOM (pre-click) | 3. Actual POST body | 4. After the response |
|---|---|---|---|---|
| `ESSCCDJ023$chk` | unchecked | unchecked, enabled | **absent from body** | unchecked |
| `ESSCCDJ023_1$chk` | unchecked | unchecked, enabled | **absent from body** | unchecked |
| **`ESSCCDJ038$chk`** | **unchecked** | **checked, but `disabled=True`** | **`on`** | checked |
| `ESSCCDJ023_hid` | no value attribute | len=1 | **`'0'`** | len=1 |
| `ESSCCDJ023_1_hid` | no value attribute | len=1 | **`'0'`** | len=1 |
| `ESSCCDJ038_hid` | no value attribute | len=1 | **`'1'`** | len=1 |
| `GridUserControl1$hdnBtnSaveEnabled` | `false` | `true` (len 4) | **`false` (len 5)** | `false` |
| `__EVENTTARGET` | empty | empty | **empty** | empty |
| `__EVENTARGUMENT` | empty | empty | **empty** | empty |
| `__MSPVSTATE` | len 8164 | len 8168, fnv `c9e2e1a3` | len 8168, fnv `c9e2e1a3` (not touched by JS) | **len 8572, fnv `0befced6`** |
| `__MSPVSTATE_ZIP` | `true` | `true` | `true` | `true` |
| `__VIEWSTATE` | len 0 | len 0 | len 0 | len 0 |
| `GridUserControl1$Button9` | `disabled`, type=submit | **`disabled=False`** (enabled by JS) | **absent from body** | disabled |
| `BtnDetailSave` | type=image, 0px, has onclick | **invisible to `form.elements`** (see below) | **`BtnDetailSave.x` + `.y`** | — |
| `DSCScriptManager` | not a field (just a string) | absent | **present, len=30** | — |
| `hdnGridData` | empty | len 0 | absent from body | **len 217** |
| `hdnGridDataCount` | empty | len 0 | absent from body | **len 1 → one row added** |
| `NowGridControlName` | empty | len 0 | absent from body | len 16 |

### The trap in each row

**`ESSCCDJ038$chk` differs in all three views**, the single most important cell in
this report:
- raw HTML: no `checked`
- after load, JS **checks it and simultaneously sets it disabled** → being disabled,
  the browser's `FormData` **excludes** it (which also explains why snapshot C's
  FormData has 117 entries while the POST has 121)
- yet the actual POST **does** contain `ESSCCDJ038$chk=on` → so the onclick handler
  chain **re-enables** it just before submitting (a common ASP.NET move, since a
  disabled control's value is lost across a postback)

**`hdnBtnSaveEnabled` goes full circle**: `false` (on load) → `true` (validation
passes, the button becomes enabled) → back to **`false`** at submit time. The
onclick chain's `SetDetailSaveButtonEnabled()` disables the button before submitting
to prevent double submission, and flips this flag back to false on the way. **A
replay must send `false`, not `true`.**

**The three `_hid` mirror fields are the real carriers of checkbox state**: in the
raw HTML they do not even have a `value` attribute, yet the POST sends `'0'`/`'0'`/`'1'`
— corresponding one-to-one with the three checkboxes' checked states.

---

## 2. What actually submits the form

`BtnDetailSave` looks like this in the raw HTML:

```html
<input type="image" name="BtnDetailSave" id="BtnDetailSave" src=""
       onclick="javascript:WebForm_DoPostBackWithOptions(
                  new WebForm_PostBackOptions('BtnDetailSave', '', true, '', '', false, false))"
       style="width:0px;border-width:0px;" />
```

`WebForm_PostBackOptions`'s last argument is `clientSubmit=false`, meaning **do not
go through `__doPostBack`** — let this button submit the form natively. A native
`<input type="image">` submits click coordinates `name.x` / `name.y`, **not**
`name=value`. Which is why:

- the POST body has `BtnDetailSave.x=1` and `BtnDetailSave.y=1`
- `__EVENTTARGET` is **empty** (no `__doPostBack` involved)
- `GridUserControl1$Button9` — the button you actually pressed — is not in the body
  at all; it is only the entry point that runs the JS, and this hidden 0-pixel button
  is what submits the form

### ⚠️ A DOM spec detail that will trip people up

Snapshot C has **128** named controls, while parsing the raw HTML yields **153** — a
difference of **25**, exactly the number of `<input type="image">` elements in the
raw HTML.

The reason: the HTML spec explicitly states that **`form.elements` excludes `input
type="image"`**.

So **any approach that derives a payload solely from the browser's `form.elements`
or `FormData` will never discover that `BtnDetailSave` exists**. Only parsing the raw
HTML reveals it. That happens to vindicate Phase 3A's choice of a raw-HTML parser
(which did pick up all 25 image inputs).

### `DSCScriptManager` reveals another layer

The POST response's `Content-Type` is **`text/plain; charset=utf-8`, 31,261 bytes**,
not HTML. Together with a `DSCScriptManager` field in the POST body that does not
exist in the raw HTML (len=30, added by JS at submit time), this means the postback is
an **ASP.NET ScriptManager asynchronous partial postback (an UpdatePanel delta)**,
not a full page reload.

**What this means for Phase 3C**: the response is not complete HTML and cannot be
handed to `parse_form()`. The ASP.NET AJAX delta format (a pipe-delimited
`length|type|id|content|…` string) has to be parsed first to extract the new
`__MSPVSTATE`.

---

## 3. CheckPeoplePower's AJAX

Triggered onblur after entering the traveler code — **4 POSTs**, all under `/HRMESS/`:

| # | Endpoint | Body | Nature |
|---|---|---|---|
| 1 | `ajaxpro/com.digiwin.erpiiplus_app.ess.ESSF21,src.ESS.ESSF21.ashx` | `{"strCode":"<code>"}` | query |
| 2 | as above | `{"pCode":"<code>"}` | query (CheckPeoplePower itself) |
| 3 | `ajaxpro/tw.com.dsc.dscDotNet.kernelBasePage.DSCBasePage,PlatformUtil.ashx` | `{"pUnid":"...","pSessionKey":"MJDscSessionValue","pSessionValue":"<root>…"}` | **writes session state** |
| 4 | `src/ESS/ESSF21/ESSF21_MIMJ.aspx` | XML `<root><title>MJ</title><MJCategory>Employee_出差人</MJCategory>…` (the category names the traveler entity) | query (Content-Type: `text/plain`) |

**#3 is the crucial one**: its parameter names are literally `pSessionKey` /
`pSessionValue` — it writes a chunk of XML into the server-side ASP.NET session under
the key `MJDscSessionValue`. That is unmistakably a **server-side state write, not
merely a query**.

Once validation completes, JS fills in 12 detail fields (`ESSCCDD004` through
`ESSCCDD015`: code, name, company/department/position IDs and so on, several of them
36-character GUIDs). Those values **can only come from the AJAX responses** and
cannot be derived.

---

## 4. The POST at a glance

| Item | Value |
|---|---|
| URL | `http://eip.example.com/HRMESS/src/ESS/ESSF21/ESSF21.aspx?...` (the form action, Identifier included) |
| Method | POST |
| Content-Type | `application/x-www-form-urlencoded` |
| Body length | 12,816 bytes |
| Field count | **121** |
| Response | 200, `text/plain; charset=utf-8`, **31,261 bytes** |
| Redirect | none |
| Dialogs | none |

### 121 vs Phase 3A's 117: which four

| Field | Why the Phase 3A payload lacks it |
|---|---|
| `BtnDetailSave.x` | image-button coordinates, produced only by an actual click |
| `BtnDetailSave.y` | as above |
| `DSCScriptManager` | added by JS at submit time; the field does not exist in the raw HTML |
| `ESSCCDJ038$chk` | unchecked in the raw HTML; checked by JS, and re-enabled only just before submitting |

Fields present in FormData but missing from the POST: **none**.

---

## 5. Answers to the eleven questions

**1. Does CheckPeoplePower issue AJAX?**
Yes, 4 POSTs (section 3). The `{"pCode":"<code>"}` one is CheckPeoplePower itself.

**2. Could that AJAX establish server-side state?**
**Not "could" — it definitely does.** #3's parameters are literally
`pSessionKey="MJDscSessionValue"` / `pSessionValue=<XML>`, an explicit server-side
session write. A pure-HTTP replay must reproduce it.

**3. Is Button9 an ordinary submit or a `__doPostBack`?**
**Neither.** It is a third mechanism: the native submit of the 0-pixel hidden image
button `BtnDetailSave`, sending `BtnDetailSave.x`/`.y`. `__EVENTTARGET` is empty and
`GridUserControl1$Button9` is absent from the body. And the whole thing is wrapped in
a ScriptManager asynchronous postback (the response is a `text/plain` delta).

**4. How many POST fields does the browser send?**
**121** (body 12,816 bytes).

**5. How does that differ from the current 117-field payload?**
Four extra: `BtnDetailSave.x`, `BtnDetailSave.y`, `DSCScriptManager`,
`ESSCCDJ038$chk`. None missing. There are also 3 fields with **the same name but a
different value**, which is more dangerous than the count difference:
`hdnBtnSaveEnabled` must be sent as `false` (not the DOM's current `true`), the three
`_hid` fields must be sent as `0/0/1` (empty in the raw HTML), and the 12
`ESSCCDD004`-`015` detail fields have to be obtained from the AJAX first.

**6. How is the `ESSCCDJ038` checkbox actually sent?**
As `ESSCCDJ038$chk=on` **and simultaneously** `ESSCCDJ038_hid=1`. Both mechanisms at
once. Both are empty in the raw HTML; JS supplies them.

**7. What are the three `_hid` values and states?**
`ESSCCDJ023_hid='0'`, `ESSCCDJ023_1_hid='0'`, `ESSCCDJ038_hid='1'`, matching the
three checkboxes' checked states (unchecked=0, checked=1).

**8. When does `hdnBtnSaveEnabled` change from false?**
It goes `false` → `true` when the traveler code is entered and validation passes (at
the same moment Button9's `disabled` goes True → False). But it is **flipped back to
`false` before submission**, and the POST sends `false`.

**9. Does JS modify `__MSPVSTATE` before the POST?**
**No.** Snapshot C and the POST body have identical fingerprints (`c9e2e1a3`, length
8168) → echoed verbatim.

**10. Does `__MSPVSTATE` update after the POST response?**
**Yes, substantially.** 8,168 → 8,572 characters (+404), fingerprint `c9e2e1a3` →
`0befced6`. Any subsequent request **must use the new value from the response and
must never reuse the old one**.

**11. Is everything in place for a Phase 3C HTTP replay?**
**Not yet** — three pieces are missing, none of which should be guessed:

| Gap | Detail |
|---|---|
| `DSCScriptManager`'s **value** | Only its length (30) was recorded, not its content (it was not on my watch list). It is the UpdatePanel ID, and the exact string is needed |
| The POST's **request headers** | A ScriptManager asynchronous postback usually needs `X-MicrosoftAjax: Delta=true`; only Content-Type was recorded this time |
| **A parser for the delta response format** | The response is 31KB of `text/plain` in a pipe-delimited format, and a parser is needed to extract the new `__MSPVSTATE` |

The four AJAX calls' **response contents** were also recorded only as lengths, so the
mapping onto the 12 detail fields has not been worked out.

---

## 6. Verifying the save

As you asked, the snapshot was taken only after `load` + `networkidle` and after
confirming both `Form1` and `__MSPVSTATE` were back (not repeating
`capture_browser_sequence.py`'s mistake of calling `.content()` too early).

| Evidence | Result |
|---|---|
| `hdnGridDataCount` | 0 → **1** (one detail row) |
| `hdnGridData` | 0 → **217 characters** |
| `NowGridControlName` | 0 → 16 |
| `__MSPVSTATE` | +404 characters |
| Detail input fields `ESSCCDD004`-`015` | all cleared (normal post-save reset behaviour) |
| Dialogs / error messages | none |
| POST response | 200 |

**Conclusion: the save succeeded.**

A note: the detail list's table is nowhere on screen (`body.innerText` is only 389
characters), because the form is currently in the `createRecord` div (single-entry
mode) and the list lives in another hidden div/tab. I did not click across to check
(that would change state) and relied on the more reliable `hdnGridDataCount` evidence
instead.

---

## 7. Three things to be upfront about

### 1. results.json once contained an employee code (remediated)

AjaxPro sends a raw JSON request body, and my logging code ran it through
`parse_qsl`, so the whole JSON string was recorded as a "field name" — putting an
employee code into a record that was supposed to hold names only, in violation of my
own stated masking rules.

Handled: all 56 occurrences were replaced with `<EMPCODE_MASKED_len6>`, leaving the
JSON structure intact and still parseable. (`logs/` was already in .gitignore, and the
same code had long appeared in a frame URL in `docs/eip-analysis.md`, so the actual
exposure risk was zero — but a rule is a rule.)

In future, logging an AjaxPro-style raw-JSON body must first check that the
Content-Type is not genuinely form-encoded, rather than applying `parse_qsl`
unconditionally.

### 2. The header was filled with test data

To stop the single allowed click from being blocked by `saveCheckD` /
`CheckDetailForm` validation, obvious dummy values were entered first (a date of
`2026/01/01`, placeholder location and reason text). Those exist only in a draft and
were never submitted. The pristine snapshot A was taken **before** that fill, so the
"raw HTML vs JS-executed DOM" comparison is uncontaminated.

### 3. (Incidentally) the long-running sign-in problem is solved

Launching debug Edge with `--auth-server-allowlist=*.example.com` this time made
**SSO complete automatically, with no manual intervention at all**.

That overturns part of `docs/login-automation-investigation.md`: it read the recurring
`chrome-error://chromewebdata/` as "Chromium's internal NTLM negotiation is
unstable", when the real cause was that this dedicated profile had no automatic-SSO
allowlist, so Edge had been popping the Windows credential dialog all along and the
error page followed from nobody answering it. The earlier test that found this
argument "ineffective" had been testing a different problem entirely (Playwright's
`page.goto()` navigation being blocked, which the allowlist does not affect).

---

## 8. Current status

- The traveler save was executed **exactly once**;
  `logs/traveler_save_capture/ALREADY_EXECUTED.marker` now exists and a re-run is
  refused
- The trip application was not submitted, `MasterPage_btnCreateToolSendForm` was not
  pressed, and `btClosejQTab` was not called
- No `requests.post()` and no HTTP replay were performed
- The production Playwright/CDP flow was not modified (no timestamp under `src/`
  changed for the pre-existing files)
- **Phase 3C was not entered**, awaiting your confirmation
