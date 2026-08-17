# Feasibility study: replacing the browser with HTTP + Windows SSPI

> **⚠️ Later update (see `docs/http-epie001-init-condition.md`)**
> This document's claim that "deriving the EPIE001 URL is not reproducible", and
> the guess that "a user may only have one in-creation tab at a time", **have
> since been explained and overturned**: the actual prerequisite is that the same
> session must GET `CollectData.aspx` first (the frame src of the `/EFNET/`
> homepage — the Step 2 crawler below happened to walk it, which is why the first
> attempt succeeded; every later probe hit TreeMainFrame/EPIE001 directly and
> skipped it). With that step added, the full EPIE001 reproduces 5/5. The content
> below is kept as the record of what was observed at the time.

**Goal**: assess whether the current `Edge + Playwright + CDP + manual/semi-automatic
sign-in` can be replaced with `Python + Windows SSPI + HTTP + ASP.NET WebForms` —
that is, whether Python can call EIP directly as the signed-in Windows user, with
no browser involved in either sign-in or form handling.

**Scope**: this document covers Phase 1 (read-only diagnosis) and Phase 2 Steps
1-3 (GET-only exploration) only. **No POST was issued**, no AD/GPO/SPN setting was
changed, and no production Playwright code under `src/` was modified. Everything
below is real output from actual runs, not inference.

---

## Phase 1: determining the authentication protocol (read-only)

### 1. Kerberos tickets (`klist`)

```
klist
```

**Careful — an environment trap found in practice**: this machine has two
`klist.exe` on `PATH`, and the Amazon Corretto JDK one sorts **ahead** of the
Windows one:

| Source | Behaviour |
|---|---|
| `C:\Program Files\Amazon Corretto\jdk21.0.9_10\bin\klist.exe` | Java/MIT style, looks for a file-based credential cache, reports `Credentials cache ... not found` (**a misleading error — it does not mean there are no tickets**) |
| `C:\WINDOWS\system32\klist.exe` (the real Windows one) | Queries the real ticket cache managed by the Windows LSA, which is the store browsers and SSPI actually use |

With the full path `& "$env:WINDIR\System32\klist.exe"`:

```
Cached Tickets: (2)

#0>  Client: youruser @ EXAMPLE.COM
     Server: krbtgt/EXAMPLE.COM @ EXAMPLE.COM
     (the TGT — normal, so Kerberos sign-in itself is fine)

#1>  Client: youruser @ EXAMPLE.COM
     Server: LDAP/dc.example.com/example.com @ EXAMPLE.COM
     (Kerberos LDAP authentication against the domain controller has happened)
```

**There is no `HTTP/eip.example.com` service ticket, or anything like it.**

### 2. SPNs (read-only query)

`setspn -Q HTTP/eip.example.com` could not connect (see the environment note
below), so a read-only .NET `DirectorySearcher` query against the Global Catalog
(port 3268, not 389) gave an unambiguous answer:

```
(servicePrincipalName=HTTP/eip.example.com)  → 0 results
(servicePrincipalName=*eip*)                 → 0 results (nowhere in the forest)
```

**No account anywhere in the AD forest has ever registered an SPN containing
"eip".**

**Environment note**: the LDAP connection `setspn.exe` uses internally (port 389)
does not work over the current network path (`Ldap Error(0x51 -- Server Down)`),
but the Global Catalog (3268) and SMB (445) do, and `nltest /dsgetdc:` locates
`dc.example.com` (10.0.0.10) fine. So the domain is reachable; it is
`setspn.exe`'s preferred connection method that is not, and querying the GC
instead works around it — **no setting was changed, this is purely a different
read-only query path**.

### 3. Edge policy (pending human confirmation)

`AuthServerAllowlist` / `AuthSchemes` in `edge://policy` have **not been requested
yet**. The Phase 2 Step 0 measurement below (the server replies
`WWW-Authenticate: Negotiate, NTLM`) already answers "what does the server
support"; `edge://policy` would only fill in the browser-side policy piece, and
can be supplied later if wanted.

### Verdict: Kerberos or NTLM?

**NTLM.** Not a guess — three independent pieces of evidence agree:

1. AD contains no `HTTP/eip.example.com` SPN, nor any SPN containing "eip", so
   Kerberos **structurally cannot** issue a service ticket for this service (the
   KDC has no matching principal).
2. `klist` shows this logon session has never held an HTTP/eip ticket, despite
   the same identity having used EIP many times.
3. The server answers anonymous requests with `WWW-Authenticate: Negotiate, NTLM`
   (measured in Phase 2 Step 0). Offering Negotiate is normal IIS default
   behaviour, but because of #1 the Negotiate exchange must fall back to NTLM and
   never reaches Kerberos.

---

## Phase 2: HTTP + SSPI explorer (`scripts/http_eip_explorer.py`)

The script only issues GETs. It prints to the console and writes structured
results (sensitive fields masked or reduced to lengths) to
`logs/http_explorer/findings.json`, with raw HTML snapshots alongside (all
gitignored).

Run: `python scripts/http_eip_explorer.py`

### Step 0: observing the auth mechanism with an anonymous request

| Item | Result |
|---|---|
| Status | 401 |
| `WWW-Authenticate` (scheme names only; the full header value is not logged) | `Negotiate`, `NTLM` |

### Step 1: SSPI-authenticated GET of the homepage

| Item | Result |
|---|---|
| Status | 200 (consistently; many requests across 3 independent script runs, **zero authentication failures**) |
| Final URL | `http://eip.example.com/EFNET/` (no extra redirects; the 401→401→200 is SSPI's own challenge-response handshake, not application-level redirection) |
| Content-Type | `text/html` |
| `Persistent-Auth` response header | `true` (consistent with the earlier SSPI experiment: this layer's authentication is bound to the connection) |
| Set-Cookie | absent from the EFNET homepage response |
| Frame count | 1 (`TreeMainFrame.aspx`) |

**An additional finding (from follow-up probing)**: crawling on to
`TreeMainFrame.aspx`, the server **does** issue an `ASP.NET_SessionId` cookie
(name recorded, value not). So the site is not entirely stateless — the EFNET
front end does use a traditional ASP.NET session.

### Step 2: the frame tree (pure HTTP, no JavaScript executed)

What the crawl actually found:

```
/EFNET/  (1 frame)
└─ TreeMainFrame.aspx  (5 frames)
   ├─ banner    → src=""  ⚠️ empty
   ├─ contents1 → tree.aspx        ✅ 200
   ├─ marquee   → Marquee.aspx     ✅ 200
   ├─ main      → src=""  ⚠️ empty
   └─ contents3 → ShowStatus.aspx  ✅ 200
```

(The empty srcs on `banner` / `main` were confirmed by reading the raw HTML tags
during follow-up probing: `<frame name="banner" id="banner" ... src=""
scrolling="no">`, and likewise for `main`.)

**This is the most important structural finding of the study**: it is not only the
trip-registration tab that needs JavaScript to come into existence — **even the
outer navigation shell (the banner menu bar, the main content area) has empty
frame srcs that JavaScript fills in after load**. Pure HTTP GET therefore never
sees `platform.aspx`, let alone `EPIE001.aspx` / `ESSF21.aspx` (all three came
back `False` in the Step 2 crawl, as expected, since they are simply not in the
server-rendered initial HTML).

### Step 3a: GET the bare path directly

```
GET http://eip.example.com/HRMESS/src/ESS/ESSF21/ESSF21.aspx
→ 302 → http://eip.example.com/HRMESS/src/_Common/AppUtil/FrameSet/SessionTimeOut.aspx
→ 200, title = "SessionTimeout"
```

No 401 (so Windows authentication itself is fine), but the application layer
judged the request to carry no valid state and redirected to the timeout page —
as expected, since it carried no `LoginId` / `TaskId` / `Identifier` parameters at
all.

This also surfaced a structural fact: `HRMESS` (where `ESSF21.aspx` lives) and
`EFNET` (where `EPIE001.aspx` lives) are **two entirely separate ASP.NET
applications** — `X-AspNet-Version` is `2.0.50727` (HRMESS, very old) versus
`4.0.30319` (EFNET). And HRMESS responses never carry a `Persistent-Auth` header.
That matters for reasoning about why the form content cannot be read; see the
Step 3c discussion.

### Step 3b: deriving the ESSF21.aspx URL from a known stable entry point (no hardcoding, no guessing)

Fixed entry point:
`http://eip.example.com/EFNET/src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21`
(that URL carries no session-specific parameters; like the CSS selector ids used
elsewhere in the project, it is a stable application entry point, not a guess and
not one user's session data hardcoded).

**First run (the script's main flow, recorded in `findings.json`): success**

- Response size 91,694 bytes
- Found directly in the response HTML: `<frame ... src="HRMESS/src/ESS/ESSF21/ESSF21.aspx?Product=true&LoginId=E12345&TaskId=ESSF21&ClientIP=10.0.0.20&Identifier=0123456789abcdef0123456789abcdef&AFormType=FRM&AFormStatus=CREATE&ProductName=EFNET">`
- That URL was **extracted from the actual response**, and the `Identifier` was
  generated dynamically by the server for that call (it differs from the
  `Identifier` observed through the browser in `docs/eip-analysis.md`, confirming
  the value really is generated per call rather than fixed).

**Follow-up: five repeat runs, all failed (not reproducible)**

To check whether that result was stable, the same GET was run five more times
(the first follow-up probe plus four repeats for `Q3`):

| Attempt | Response size | Body contains ESSF21.aspx |
|---|---|---|
| 2 | 15,275 bytes | no |
| 3 | 15,275 bytes | no |
| 4 | 15,275 bytes | no |
| 5 | 15,275 bytes | no |
| 6 | 15,275 bytes | no |

**This URL derivation is currently not reliably reproducible** — it worked once,
on the very first attempt, and afterwards consistently returned a much smaller
version with no ESSF21 link. The most likely hypothesis at this point (unproven):
EPIE001.aspx may hold server-side state along the lines of "one in-creation tab per
user per form type" — the first call triggers the open-a-new-tab logic and returns
the full content, while later calls detect "already opened" and return the slim
version. That is **a different kind of thing entirely** from Chromium's block on
NTLM SSO for CDP navigations described in
`docs/login-automation-investigation.md`: that is a browser-engine-level,
unconditional security boundary, whereas this looks like **the application's own
business-logic state**, which in principle might be resettable or bypassable. The
trigger condition has not been found yet and needs more experiments (see "smallest
next experiments" below).

### Step 3c: GET the derived URL and inspect the form fields

**Two attempts (the original run plus a follow-up retry with the same URL), both
identical:**

```
Status:         200
Content-Length: 0
Content-Type:   (absent entirely)
```

**The server returned a completely empty 200** — not an error page, not a
redirect. Adding a `Referer` (as a browser would when loading a child frame), a
browser-style `User-Agent`, and `Sec-Fetch-Dest: iframe` all produced the same
empty 200 — **none of those headers is the deciding factor**.

The more plausible reading (taken together with Step 3b's non-reproducibility) is
that the `Identifier` is a **single-use or very short-lived** token, already
expired by the time Step 3c used it (within the same script run, less than a
second later), rather than a missing HTTP header. **So far the real ESSF21.aspx
form content has never once been read**, which is why the existence of fields like
`ESSCCDJ024_txt` and WebForms hidden fields like `__VIEWSTATE` could not be
confirmed over pure HTTP. On this point Phase 2 Step 3 is **not yet successful**
rather than failed: it is stuck on a state-lifetime problem that looks solvable
but has not been solved.

---

## Answers to the eight questions asked

**1. Does EIP actually use Kerberos or NTLM?**
NTLM. AD holds no `HTTP/eip*` SPN (structurally ruling out Kerberos), `klist` has
never shown a matching ticket, and although the server offers `Negotiate` it must
fall back to NTLM. Three independent pieces of evidence agree, so confidence is
high.

**2. Does SSPI reach the homepage reliably?**
Yes, very reliably. Three independent script runs, over eight requests in total,
every SSPI authentication successful — zero failures, zero timeouts. That is
markedly different from the "CDP-driven Edge sign-in flips between success and
failure" recorded in the other report: **for the sign-in step, pure HTTP + SSPI
currently looks considerably more stable than the browser route.**

**3. Can ESSF21 be reached by following the frame structure?**
Partly, but unreliably. The homepage's own navigation shell (banner/main) needs
JavaScript to populate, so pure HTTP sees nothing there. But going one level
deeper and hitting the known `EPIE001.aspx?FormID=ESSF21` entry point did, on the
first attempt, return a complete, dynamically generated, non-guessed ESSF21.aspx
URL from the server's response — proving the path can in principle be walked
without JS. Five repeats could not reproduce it, suspected to involve server-side
state like "one in-creation tab per user".

**4. Can the real form fields be read?**
Not yet. GETting the one successfully derived URL returned an empty 200
(Content-Length: 0), and Referer / User-Agent / Sec-Fetch headers did not change
that. The current reading is that the URL's `Identifier` is single-use or very
short-lived, rather than a header being missing.

**5. Can the ASP.NET hidden state be parsed?**
No chance to check yet — because of #4 there has been no response containing form
content, so `__VIEWSTATE` and friends currently read as absent. That is only
because the response itself is empty; it says nothing about whether the technique
works.

**6. How feasible is HTTP automation overall?**
Two layers. **Sign-in / authentication: highly feasible** — the access SSPI
obtains is equivalent to a real browser's, and more stable than the CDP route.
**Reaching specific form content: undetermined** — blocked on what looks like an
application business-logic state problem rather than a security boundary, which by
nature stands a better chance of being solved than "Chromium blocks NTLM SSO for
CDP navigations", but needs targeted experiments before anything is claimed either
way.

**7. What are the smallest next experiments?**
Three low-cost, observation/GET-only experiments (none of which need a POST or
touch the production flow):
   - **(a) Use the existing Playwright/NetworkRecorder to watch the request a real
     browser issues to load the framePlus frame when a person clicks the trip
     shortcut** (purely passive observation of a real browser, no form
     submission), to confirm there is really no header or cookie being missed.
   - **(b) Shorten the gap between Step 3b and 3c to near zero** (already fast, but
     the requests could be pipelined on one TCP connection, or at minimum verified
     to have nothing in between), ruling out the simplest explanation — that we
     were just too slow.
   - **(c) Test whether calling `btClosejQTab`'s backend logic between two
     EPIE001.aspx calls (if it has its own URL) lets the next GET return the full
     content again** — a direct test of the single-tab-lock hypothesis.

**8. Is there still a reason to work on CDP sign-in?**
Yes, keep it for now. The CDP route is the only path that has ever gone all the
way to a successful submission. The HTTP/SSPI route has so far only shown that the
sign-in layer works and is more stable; it has not shown that the form can be read
reliably, never mind filled in and submitted. Both lines should continue in
parallel without interfering — this exploration modified no production file under
`src/`, leaving the Playwright/CDP route untouched.

---

## Current status

Phase 1 and Phase 2 Steps 1-3 are complete. Stopping here as instructed: **not
entering Phase 3 (the WebForms state parser), issuing no POST to any page**,
awaiting further direction.
