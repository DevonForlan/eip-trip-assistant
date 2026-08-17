# EIP automatic sign-in: investigation report

> ## ⚠️ Correction, 2026-08-14: this document's central conclusion was wrong
>
> **The problem is solved.** One argument on the debug Edge launch line is all it took:
>
> ```
> --auth-server-allowlist=*.example.com
> ```
>
> Measured result: `browser.attach_context()` **completes sign-in automatically in
> 3.4 seconds, with zero human intervention and no credential dialog at all**.
> The argument is now part of `edge_launch_args()` in `src/browser.py`.
>
> **The original misdiagnosis**: this document read the recurring
> `chrome-error://chromewebdata/` as "Chromium's internal NTLM negotiation is
> unstable" and "it keeps oscillating between success and failure", and concluded
> from that that software alone could never reach 100% — that only IT could fix it,
> by configuring Kerberos constrained delegation.
>
> **The actual cause**: this project's dedicated `.edge-profile` did not inherit
> the automatic-SSO allowlist policy that the user's everyday Edge has, so
> Chromium refused to send Windows credentials automatically and popped the native
> "Windows Security" credential dialog instead. During an automated run nobody was
> there to answer it → the request never authenticated → the tab landed on the error
> page. The "oscillation between success and failure" I observed was that dialog
> appearing and disappearing, not a network-layer problem.
>
> **Why section 2 below calls this argument ineffective**: because what it tested
> was a **completely different problem** — Chromium blocking a Playwright-initiated
> `page.goto()`. That block has nothing to do with the allowlist, and no argument
> can lift it. Conflating the two was the biggest methodological failure in this
> investigation.
>
> Section 2 and the parts of the conclusion arguing "this needs infrastructure
> work by IT" **no longer apply**. The remaining observations (the CDP navigation
> block, SSPI's connection binding, pywinauto's foreground lock) still hold.

**Goal of the investigation**: EIP uses Windows Integrated Authentication
(NTLM/Negotiate). Opening Edge by hand signs in with no password prompt at all,
yet automation through Playwright could never complete sign-in. This document
records **every** approach tried, what each one did, and the technical reason
behind it.

**Conclusion up front**: the only partially working approach found so far is
launching the browser externally with the URL as a command-line argument and
attaching over CDP afterwards, but it **cannot be made 100% reliable**, and nine
different technical angles have ruled out the alternatives. Truly
intervention-free sign-in would need IT / the domain administrator to configure
it at the infrastructure level (a service account with Kerberos constrained
delegation), which no script can do on its own.

---

## Background: the nature of the problem

EIP is a legacy ASP.NET / IIS system using **Windows Integrated Authentication**:
your identity is the Windows account currently signed in on this machine, handed
over via a network-level NTLM or Negotiate (Kerberos) handshake. There is **no
web login form and no password field**, which is why opening Edge normally signs
you in without noticing.

The problem is a deliberate Chromium security measure: **once a browser tab has
been taken over via CDP** (the Chrome DevTools Protocol that Playwright, Puppeteer
and friends use to control a browser remotely), **no navigation in that tab will
trigger automatic NTLM/Negotiate SSO**. That exists to stop malicious automation
from silently borrowing the user's Windows identity to reach internal systems. It
is an intentional security boundary, not a bug.

---

## Everything that was tried

| # | Approach | Result | Root cause |
|---|---|---|---|
| 1 | Playwright `launch()` + `page.goto()` | ❌ Fails (`ERR_INVALID_AUTH_CREDENTIALS`) | CDP navigation is blocked unconditionally |
| 2 | Force SSO with the `--auth-server-whitelist` argument | ❌ Fails, same error | The whitelist governs *whether to attempt* automatic SSO; it does not lift the block on CDP navigation, and on failure the browser does not fall back to the native credential dialog either |
| 3 | `connect_over_cdp()` onto an Edge launched externally with the URL as an argument | 🟡 **Partly works, unreliable** | The navigation happens before Playwright takes over, so SSO can fire; but success depends on network conditions and Chromium's internal negotiation timing, and the tab was observed flipping between success and failure |
| 4 | Simulate a real link click instead of `.goto()` (to test whether a user gesture matters) | ❌ Fails, same error | Confirms the block is not about *how* you navigate but about *whether the tab was ever taken over by CDP* — afterwards, every navigation method is blocked |
| 5 | `launch_persistent_context(channel="msedge")` to run **real** Microsoft Edge | ❌ Fails, same error | Confirms the block is unrelated to "is this real Edge" and "does it pick up corporate GPO policy"; only "did Playwright initiate the navigation" matters |
| 6 | OS-level keyboard simulation (`pywinauto` / Windows UI Automation) driving the address bar of an already-open window | ❌ Fails (`SetForegroundWindow` has no effect) | Windows deliberately restricts this: a foreground-focus grab called by a background process without user action is routinely ignored, so malware cannot steal focus from the window the user is working in |
| 7 | `requests_negotiate_sspi`: issue HTTP requests through Windows SSPI, no browser involved | 🟡 **HTTP authentication itself works 100%**, but nothing carries over to a browser | The server replies `Persistent-Auth: true` with no `Set-Cookie` — authentication is bound to the TCP connection itself, not to a cookie or token, so there is no "thing" to hand a browser |
| 8 | Launch the browser via WMI (`Win32_Process.Create`) instead of `subprocess.Popen`, to rule out the process chain | ❌ Fails, exactly as unreliably as before | Rules out process-creation method / parent-process chain as the cause of the instability |
| 9 | Increase retries and watch the stability pattern across many launches | 🟡 Observed **continuous flipping between success and failure** on a 10-15s cycle, not "stable after N retries" | Something underneath is continuously negotiating/retrying; the problem is live network/auth negotiation state, not a one-off failure that waiting out would fix |

Also checked and ruled out:
- **Edge secure DNS (DoH)**: the profile's settings file showed it was not
  explicitly enabled, making it an unlikely cause in the default mode.
- **Network connectivity itself**: `nslookup`, `curl` and SSPI requests confirmed
  repeatedly that the network path (VPN / DNS) was up throughout. The problem was
  never connectivity.

---

## Each approach in detail

### Approaches 1-2: direct navigation / a command-line allowlist

The first attempt: let Playwright launch the browser and call
`page.goto(EIP_URL)`. Immediately:

```
playwright._impl._errors.Error: Page.goto: net::ERR_INVALID_AUTH_CREDENTIALS
```

Adding `--auth-server-whitelist=*.example.com
--auth-negotiate-delegate-whitelist=*.example.com` — the mechanism enterprises
normally push via GPO to enable automatic SSO — failed identically. So even when
Chromium is told explicitly that this domain may sign in with Windows
credentials, that permission is not applied in a CDP-controlled tab.

### Approach 3: launch externally, attach afterwards (the only partly working route)

A change of tack: don't let Playwright initiate the navigation. Launch
`msedge.exe` with an ordinary `subprocess.Popen` and pass the target URL as a
**command-line argument**:

```
msedge.exe --remote-debugging-port=9222 --user-data-dir=<profile> "http://eip.example.com/EFNET/"
```

That navigation is handled by the OS/browser's own startup logic, never touching
CDP, so SSO fires normally. Only after the browser has signed in does
`playwright.chromium.connect_over_cdp()` attach to read and drive the DOM.

This approach **demonstrably works** — several successes so far, including two
real trip registrations submitted — but it is **unreliable**: with the same
command, it sometimes succeeds within seconds and sometimes lands on a transient
error page (`chrome-error://chromewebdata/`). The same tab was observed flipping
between the two states for 10-15 seconds or more before possibly settling (or
staying unsettled).

### Approach 4: testing the user-gesture theory

Hypothesis: perhaps the deciding factor is whether a real user gesture triggered
the navigation, not CDP itself. Test: in a tab Playwright had already taken over,
skip `.goto()` and use Playwright's `.click()` on a real `<a href>` link
(`.click()` dispatches genuine mouse events, which is protocol-level closer to a
real click).

Result: the same `ERR_INVALID_AUTH_CREDENTIALS`.

**Conclusion**: the deciding factor is not "was this navigation simulated" but
"has this tab ever been taken over by CDP". Once Playwright connects to a tab,
**every** subsequent navigation method — `.goto()` or a simulated click — is
blocked. That is also why the ordering "open and sign in by hand first, attach
only afterwards" is not optional: after attaching, there is no going back.

### Approach 5: real Microsoft Edge

Hypothesis: perhaps the block targets only Playwright's bundled Chromium, and
launching the **actually installed** Microsoft Edge via `channel="msedge"` (which
does pick up corporate GPO policy) would behave differently.

Test: `playwright.chromium.launch_persistent_context(user_data_dir=...,
channel="msedge", headless=False)`, then `page.goto(EIP_URL)`.

Result: the same `ERR_INVALID_AUTH_CREDENTIALS`, with a blank error page even in
the screenshot.

**Conclusion**: the block is unrelated to bundled-vs-real Chromium and to GPO
policy. If Playwright initiated the navigation, it is blocked regardless of which
browser executable is running. That also means swapping `connect_over_cdp()`
(which the official docs admit has lower fidelity) for a more "proper" connection
method would not get around the NTLM wall, because the wall does not care how you
connected.

### Approach 6: OS-level keyboard simulation

Reasoning: if even a simulated click does not count as a user gesture, use an
input path entirely outside CDP — Windows' UI Automation API (`pywinauto`) to send
"Ctrl+L to focus the address bar → type the URL → Enter" to an already-open
browser window. Those are OS-level keyboard events, in principle
indistinguishable from a real person at the system level.

Steps:
1. `pywinauto.Application.connect(process=<pid>)` to reach the window
2. `win32gui.SetForegroundWindow(hwnd)` to bring it to the front
3. `pywinauto.keyboard.send_keys()` to send keys

Result: `SetForegroundWindow` never really took effect — UI Automation reported
the window element as not enabled (`ElementNotEnabled`), and the keystrokes never
showed up on screen.

**Why**: Windows deliberately restricts this. **A `SetForegroundWindow` call from
a background process, without user action behind it, is frequently ignored or
only partially honoured.** The point is to stop malware from stealing focus from
the window a user is working in (say, by popping a fake dialog to harvest a
password). Our Python program starts from a terminal / background process and has
no "the user just interacted with me" standing to claim the foreground, so the
system does not route focus or input to the target window even though the API was
called.

### Approach 7: HTTP requests directly through SSPI

Reasoning: NTLM/Negotiate is not a browser feature — it is Windows' SSPI
(Security Support Provider Interface). With the `requests_negotiate_sspi`
package, Python can issue HTTP requests to EIP as the currently signed-in Windows
user with no browser at all:

```python
import requests
from requests_negotiate_sspi import HttpNegotiateAuth

session = requests.Session()
session.auth = HttpNegotiateAuth()
resp = session.get("http://eip.example.com/EFNET/")
```

Result: **the HTTP request succeeds outright** (status 200, not 401). But the
response headers show:

```
Persistent-Auth: true
```

and there is **no `Set-Cookie` whatsoever**.

**Why**: this confirms EIP's authentication is **bound to that one TCP
connection** (IIS's NTLM Persistent Authentication), not tracked by a cookie or
token. So even with a successful SSPI authentication on this side, there is no
"thing" to hand to a Playwright-driven browser — no cookie for
`context.add_cookies()`, no token to copy. The authenticated state lives and dies
with that connection, and vanishes when the Python process exits. This is a clean
**technical negative result**: the route is not merely unproven, there is
genuinely nothing transferable.

### Approach 8: creating the process via WMI

Reasoning: maybe the way we launch the browser is itself the problem. Currently
`msedge.exe` starts at the end of a deep nesting — terminal tool → Git Bash →
Python → `subprocess.Popen` — so perhaps some environment-variable or token
inheritance detail affects whether Chromium considers the launch trustworthy.
Using WMI's `Win32_Process.Create` makes the new process's parent the WMI
Provider Host (an entirely different system service) instead of our shell:

```powershell
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine = "..."}
```

Result: exactly as unreliable, no different from `subprocess.Popen`.

**Conclusion**: the process-creation method and parent-process chain are ruled out
as causes. The problem is not how we start the process, but timing instability
inside Chromium's NTLM/Negotiate handling after it starts.

### Approach 9: more retries, and watching the stability pattern

The last test: run the "close everything and relaunch on failure" retry logic
through several rounds, and **poll the same tab's state repeatedly** to see
whether it fails once and then settles, or keeps changing.

Result: the same tab was observed **flipping back and forth** between the correct
URL and `chrome-error://chromewebdata/` over a span exceeding 10-15 seconds, with
the next poll quite likely to be back in the error state. Not the pattern of "one
failure, wait a bit, then stable success".

**Conclusion**: something underneath is continuously retrying or renegotiating
(plausibly related to domain-controller response times, Kerberos ticket cache
state, or local network-interface changes). The problem is live network/auth
negotiation state — black-box behaviour that a Python script can neither observe
nor control from outside. Simply retrying more or waiting longer cannot guarantee
a fix; it only raises the odds of landing in a stable window by chance.

---

## Why "just retry a lot" is not a good answer

Worth stating explicitly: in theory enough retries would eventually succeed, yet
"retry forever until it works" was deliberately not adopted, because:

1. **It puts needless load on the corporate network and server.** A burst of
   repeated NTLM authentication attempts is not good network citizenship, even
   though it triggers no lockout (confirmed).
2. **It cannot distinguish "almost there" from "this environment won't work right
   now".** The observed flipping means there is no stable signal for "wait a
   little longer" versus "today is not the day", so blind retrying may just burn
   time.
3. **It is out of proportion to the goal.** Sign-in automation is not the user's
   objective; submitting the trip application is. When automatic sign-in stalls,
   signing in by hand takes a few seconds — more efficient than letting the
   program keep trying.

---

## Conclusion, and the only true 100% fix

**As it stands**: purely software-side, script-level means cannot guarantee
intervention-free sign-in. Nine technical angles were verified: navigation method
(direct vs simulated click), browser (bundled Chromium vs real Edge), connection
layer (CDP vs native SSPI HTTP), input method (CDP vs OS keyboard simulation), and
process creation (subprocess vs WMI). Each produced a definite reason for
failure. This is not "the right approach hasn't been found yet" but **confirmation
that these approaches are architecturally dead ends**.

Genuinely 100% automatic sign-in with no human involvement would need **IT / the
domain administrator to configure it at the infrastructure level**: a service
account granted a legitimate token for EIP via **Kerberos constrained
delegation**. That needs no browser UI and no manual sign-in, and it is standard
practice for enterprise RPA — but it requires AD / server-side changes, which no
Python script can make, so it would have to be discussed with the IT department.

---

## How the code handles this today (implemented)

Pending a possible infrastructure-level fix, the code takes a "try hard, fall
back to manual gracefully" approach:

- `browser.attach_context()` launches and waits for sign-in to settle, with retries
- If automation does not succeed within the time limit, it prints the manual
  command clearly so the user can open a browser and sign in once themselves
- After sign-in, everything downstream — opening the form, filling it in,
  duplicate checking, sending, verifying the result — is fully automatic. Sign-in
  is the one step that occasionally needs a human.
