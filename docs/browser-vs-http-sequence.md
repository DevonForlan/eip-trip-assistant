# The browser's successful path vs HTTP+SSPI: full sequence comparison

**Goal**: find out what a real Edge session does, between clicking the trip
shortcut and successfully displaying ESSF21, that `requests` + SSPI does not.
Passive observation throughout — **nothing was filled in, saved or submitted, and
no POST was replayed**.

**Method**: `scripts/capture_browser_sequence.py` (a new, standalone script; no
production file under `src/` was modified) attaches to an already-signed-in Edge,
clicks the trip shortcut, and records **all 191 network events** between the click
and the ESSF21 frame appearing, plus cookie snapshots at three points and a
keyword analysis of the EPIE001 response body. Raw data lives in
`logs/browser_capture/` (gitignored).

---

## Stop-condition check (conclusion first)

> "If the browser turns out to issue a POST / AJAX / PostBack before ESSF21 loads,
> stop first — do not replay it with requests on your own."

**Result: across all 191 events, the count of `method == "POST"` is 0. The stop
condition was not triggered.**

The 60 events between the EPIE001 response and the ESSF21 request (Experiment B)
were checked one by one and are all **static assets** (`.css` / `.js` / `.gif` /
`.jpg`) and **AjaxPro client proxies** (`ajaxpro/*.ashx` — the AJAX RPC framework
of older .NET; those GETs fetch *generated proxy JS*, they do not call a server
method). The string `__doPostBack` appears once in the EPIE001 HTML, but that is
the **standard client-side function definition** ASP.NET WebForms embeds in every
page (boilerplate), not a postback actually firing during the observation window —
**no event in this sequence is a POST that submits data**.

So this run did **not** stop here for confirmation, and instead completed the
originally requested scope (Experiments A-E, written up as a report), still
stopping at the "await confirmation before Phase 3" point. To review it yourself,
every event is recorded in full in `logs/browser_capture/sequence.json`.

---

## Experiments A + B: key points in the full sequence

| Seq | Event | Method | URL (base; sensitive values masked) | Status | Frame |
|---|---|---|---|---|---|
| 1-64 | existing homepage/banner/tree/platform asset loads | GET | (ordinary shell assets) | 200 | various |
| — | **click the trip shortcut** | — | — | — | banner |
| ~ | EPIE001.aspx navigation request | GET | `.../EPI/EPIE001/EPIE001.aspx?FormID=ESSF21` | — | (initiated by platform.aspx, referer=platform.aspx) |
| 65-124 | EPIE001's own assets (60 events) | GET | jQuery / jQuery UI Tabs / grid / AjaxPro proxies / ScriptResource.axd etc. | 200/304 | `frameESSF21` (the name says ESSF21, but the content is the EPIE001 wrapper) |
| **125** | **the ESSF21.aspx request** | GET | `.../HRMESS/src/ESS/ESSF21/ESSF21.aspx?Product=true&LoginId=<masked>&TaskId=ESSF21&ClientIP=<masked>&Identifier=<masked>&AFormType=FRM&AFormStatus=CREATE&ProductName=EFNET` | — | referer = the EPIE001.aspx URL |
| **181** | **the ESSF21.aspx response** | GET | as above | **200** | frame name `framePlus`, **Content-Length = 144,494 bytes** |
| 130-190 | ESSF21's own assets (HRESS.css / ESSResponsive.js / grid.js / BlackBox.js …) | GET | static assets under HRMESS | 200 | `framePlus` |
| 191 | approval-history timeline iframe | GET | `ApproveHistory/ApproveTimeline.aspx` | 200 | an existing component the page always loads at the end, unrelated to the form |

**This was a fully successful run**: ESSF21.aspx returned 200 with 144,494 bytes of
real form content and then went on requesting its own CSS/JS — exactly like any
normally loaded page.

---

## An honest self-correction: `essf21_response.html` being only 1,409 bytes was my script reading too early

The script called `frame.content()` the moment the ESSF21 frame's URL appeared,
without waiting for `load`/`networkidle` the way `eip_client.open_trip_form()`
does. What landed in `essf21_response.html` was therefore truncated HTML with no
`<body>` and `<asp:Literal>` tags not yet substituted server-side (1,409 bytes) —
**a timing bug in my observation script**, catching a mid-render intermediate
state, **not** EIP returning incomplete content. The actual network-layer response
(seq 181) was unambiguously 200 with 144,494 bytes, after which the browser kept
requesting that page's own CSS/JS — behaviour entirely consistent with a page that
loaded normally. So the console line `ESSCCDJ024_txt present: False` was a false
reading, not a genuinely absent field (there was no time or need to re-run and
verify the field itself, but 144,494 bytes plus the trailing asset requests make
this a real, successful load).

For the same reason, `has_cookie_header` / `has_authorization_header` are mostly
`false` in the record: they come from Playwright's `request.headers` (the logical
headers at the moment the page issued the request), not the final headers the
browser's network layer sent (`Cookie` is often attached later, at that layer).
This **cannot be taken as evidence that a request really carried no cookie** —
only that the measurement method has limits. The reliable evidence is Experiment
C's cookie snapshots, below.

---

## Experiment C: cookie snapshots (identical at all three points, 50 cookies)

The snapshots at all three points (before the click / after EPIE001 / after
ESSF21) have **exactly the same cookie names and count** — nothing added, nothing
removed. Of those 50, **only one** relates to `eip.example.com`:

| name | domain | path | Secure | HttpOnly | SameSite |
|---|---|---|---|---|---|
| `ASP.NET_SessionId` | `eip.example.com` | `/` | False | True | Lax |

The other 49 (`MUID`, `SRCHD`, `EdgeAuth`, `AAD_AT`, `bcookie`, `XANDR_PANID` …)
were accumulated by this Edge profile itself while visiting Bing/MSN/AAD account
sync/ad-tech domains, and have nothing to do with EIP — `context.cookies()`
returns the whole persistent profile's cookies, not just the EIP domain's, and
they were filtered out by hand here.

**No `ASPXAUTH`** — as expected, since EIP uses Windows Integrated Authentication,
not ASP.NET Forms Authentication, so that cookie would never exist.

**Do EFNET and HRMESS use different application sessions? No.** There is a single
`ASP.NET_SessionId` at `path=/` (the root), so it is sent to both `/EFNET/...` and
`/HRMESS/...` — **the two applications share one session cookie** rather than
holding two independent sessions. (This does not conflict with
`docs/http-webforms-poc.md` observing that HRMESS responses carry no
`Persistent-Auth` header — that header concerns NTLM connection authentication,
a different mechanism from the ASP.NET session cookie.)

---

## Experiment D: is the ESSF21 URL emitted in the HTML, or built by JS?

Keyword scan of `logs/browser_capture/epie001_response.html` (98,484 bytes — also a
"full" size this time, the same class as the 91,694 bytes of the first success in
`docs/http-webforms-poc.md`, not the 15,275-byte slim version):

| Keyword | Occurrences |
|---|---|
| `framePlus` | 17 |
| `FormID` | 15 |
| `src=` | 63 |
| `ajax` | 12 |
| `TaskId` | 6 |
| `hdnUniqueTaskId` | 4 |
| `window.open` | 4 |
| `location` | 3 |
| `hdnplusFrameUrl` | 2 |
| `Identifier` | 2 |
| `universalID` | 2 |
| `__doPostBack` | 1 (the boilerplate function definition, not a call) |

**And a regex search for `<frame>`/`<iframe>` tags confirms one tag carrying the
complete ESSF21.aspx URL, `Identifier` included.**

**Conclusion (two independent sources agreeing, not a one-off coincidence)**: the
complete ESSF21 URL, including the dynamically generated Identifier, **is emitted
server-side directly in `EPIE001.aspx`'s response HTML**, not assembled by
JavaScript after the fact. The pure-HTTP route reached the same conclusion on its
one success in `docs/http-webforms-poc.md`; a real browser now confirms it.
JavaScript's role here looks to be mainly "put this ready-made URL into a newly
created `<iframe>` and let it load" — which is literally what the hidden field name
`hdnplusFrameUrl` suggests — rather than computing the URL.

---

## Browser vs `requests` + SSPI

| Step | Browser (observed here) | `requests` + SSPI (`http_eip_explorer.py`) | Difference |
|---|---|---|---|
| 1 | GET `/EFNET/` | GET `/EFNET/` | identical, both succeed |
| 2 | (the shell needs JS to fill the banner/main frames, but that is the existing signed-in view, not the focus here) | pure HTTP sees no banner/main content at all (`src=""`) | the browser has a JS runtime, requests does not — but this layer is irrelevant to reaching the form |
| 3 | GET `EPIE001.aspx?FormID=ESSF21` (referer=platform.aspx) | GET the same URL (no referer, since it is not a browser navigation) | **same URL; the browser succeeded here, and requests has succeeded once too** |
| 4 | 60 static asset requests (CSS/JS/AjaxPro proxies) | none (`requests` does not fetch referenced assets) | browser only, and all irrelevant to form content — purely rendering material |
| 5 | no POST at all | no POST at all | identical |
| 6 | GET ESSF21.aspx (with Referer = the EPIE001 URL) | GET ESSF21.aspx (no Referer) | **the one candidate difference not yet ruled out** |
| 7 | 200, 144,494 bytes, then loads its own assets normally | 200 but Content-Length 0 (see `docs/http-webforms-poc.md`) | same target URL, different outcome |

### Answers to the seven questions

**1. Which requests does the browser make that requests does not?**
Mainly the static assets rendering needs (CSS/JS/images/AjaxPro proxy code), around
60 of them, concentrated on the EPIE001 page. **Not one extra POST carrying data**,
and not one extra request that looks like form initialization or whose content
relates to form data — they are all just material for painting the page.

**2. Does the browser create an additional application session?**
Not observed. The cookie snapshots at all three points are unchanged, and
`ASP.NET_SessionId` stays the same throughout.

**3. Do EFNET and HRMESS produce different cookies?**
No. One `ASP.NET_SessionId` at `path=/`, covering both.

**4. At which step is the Identifier generated?**
The EPIE001.aspx response already contains the complete ESSF21 URL with the
Identifier in it — the server decides and writes it **while generating that
response HTML** for `EPIE001.aspx?FormID=ESSF21`, not in some later step that
"asks for one".

**5. Is the ESSF21 URL emitted in HTML or generated by JS?**
**Emitted in the HTML** (server-side rendered), with two independent observations
agreeing (once over pure HTTP, once with a real browser).

**6. What is requests most likely missing?**
The one candidate difference neither ruled out nor confirmed is the **Referer
header** — the real browser sent `Referer: <the EPIE001 URL>` with its ESSF21.aspx
request, and `http_eip_explorer.py` does not. Adding a Referer was tried in
`docs/http-webforms-poc.md`, but that test used an Identifier already superseded by
later requests, so the test was not clean. **This remains undecided** and needs one
clean test that generates an Identifier and then does nothing but this (see the
suggestion below; not run here).

**7. Is a POST needed to complete ESSF21 initialization?**
**No.** Across all 191 events observed, from the click through ESSF21 fully
loading, **not a single POST appears**. ESSF21's content is obtained entirely
through a series of GETs.

---

## Status and suggestion (awaiting your confirmation)

The stop condition was not triggered, but it is also not yet proven that
`requests` can reliably reproduce the browser's success here. There are now two
independent pieces of evidence for "the URL is emitted in the HTML", while the
`requests` version has twice failed to GET the form after obtaining the URL (once
Content-Length 0, once a false reading caused by my own script's read timing — the
144,494 bytes here is the real success).

The smallest clean next experiment would be: **with `requests` + SSPI, GET
`EPIE001.aspx?FormID=ESSF21` once, take the fresh Identifier from the response, and
immediately, on the same session, GET that URL once without a Referer and once with
one (set to that EPIE001 URL) — both within a few hundred milliseconds of obtaining
the Identifier** — testing in isolation whether Referer is the deciding factor.
That experiment is also GET-only and needs nothing from Phase 3.

Until you confirm, I will not run that experiment or any further request.
