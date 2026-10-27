# EIP Trip Registration Automation

Fills in and submits the business-trip registration form on a corporate EIP portal
(Digiwin EasyFlow / ERPII Plus family).

Python + Playwright driving an already-logged-in Edge, plus a separate pure
HTTP + Windows SSPI route that can read the form without a browser at all.

> **Every configured value is a placeholder.** Hostnames, employee codes,
> document numbers and internal IPs throughout the code and docs are RFC 2606
> placeholders like `example.com`. Talking to a real system requires creating
> your own `.env`.

---

## Why this is harder than it looks

Legacy ASP.NET WebForms systems have a few traps that general automation
tutorials never mention. Each of these was reproduced and recorded in `docs/`:

| Problem | Finding |
|---|---|
| A Playwright-launched browser cannot authenticate (`ERR_INVALID_AUTH_CREDENTIALS`) | Chromium deliberately blocks automatic NTLM SSO for pages a CDP client has taken over. The fix is to pass the URL as a **launch argument** and attach afterwards |
| A dedicated profile keeps popping the Windows credential dialog | `--auth-server-allowlist` was missing. With it, sign-in is fully automatic |
| Pure HTTP only ever gets the slim version of the form | The same session must GET `CollectData.aspx` first. Holding a SessionId does **not** mean initialization happened |
| The form responds 200 with 0 bytes | `Accept-Language` was missing. The page has I18N logic that emits nothing at all when it cannot determine a language |
| `__VIEWSTATE` is empty | This system replaces standard ViewState with its own (compressed) `__MSPVSTATE` |
| What actually submits the "save" button | Neither that button nor `__doPostBack`, but a 0-pixel hidden `<input type="image">` |
| CDP hangs after a successful handshake | A long-running debug Edge can reach a state where the websocket connects but enumerating targets never returns. Detection and automatic restart are built in |
| The document tracking list shows stale data | The browser's draft folder serves cached results and misses a just-created document, so duplicate checking queries both the browser and an independent HTTP source |

The full investigation is in [`docs/`](docs/).

---

## Install

```powershell
pip install -r requirements.txt
playwright install chromium
```

Windows only: sign-in depends on Windows Integrated Authentication
(NTLM/Negotiate) and SSPI.

## Configure

```powershell
copy .env.example .env
```

Edit `.env`. Only `EIP_URL` is required — every other hostname is derived from it:

```
EIP_URL=http://your-eip-host/EFNET/
EIP_AUTH_ALLOWLIST=*.your-domain
```

`.env` is gitignored. **This tool never reads, stores or transmits a password**;
sign-in is always performed by the browser via Windows Integrated Authentication.

## Use

```powershell
python src/main.py
```

It prompts for the trip date, times, location and reason, then:

1. Prints a summary of your input → requires `y` to continue
2. Checks the drafts folder on the server for an existing document on the same date
   and time, and **aborts if it finds one**
3. Starts a freshly signed-in Edge, opens the form, fills it in
4. Adds the traveler
5. **Reads the actual values back off the browser and displays them** → requires a
   second `y` before clicking send

Any answer other than `y` stops immediately, leaving the form on screen unsent.

### Missed punch (補刷卡申請)

```powershell
python src/punch_main.py
```

Prompts for the date, one to six punch times, the reason (忘記刷卡 / 未發卡片 / 其他)
and an optional note, then follows the same steps: a server-side check for an
existing missed-punch form on that date, filling the live form, reading it back,
and a second `y` before sending.

## Safety design

This tool performs a real, **irreversible** submission, so several deliberate
limits are in place:

- **Two-stage confirmation**: before sending, field values are read back off the
  live browser rather than echoing the variables you typed
- **Duplicate protection**: the drafts folder is queried over HTTP before the
  browser signs in (the browser's own list serves stale, cached data); a match
  aborts the run, and so does a query that cannot be answered. It has to run
  first: EIP allows one session per user, and the HTTP sign-in ends any browser
  session already open
- **An explicit state machine** (`src/state_machine.py`): an expired session is a
  hard stop, and **nothing is ever resubmitted automatically**
- **Classified dialog handling** (`src/dialog_handler.py`): beforeunload is
  auto-accepted; confirm is accepted only when the message contains none of the
  "already exists / duplicate / overwrite / error / failed" keywords; alert and
  prompt are never auto-accepted
- **Submission verification** (`verify_submission`): success is judged from the
  document number and the read-only redirect, never from "the screen went blank".
  An UNKNOWN result is then checked against the server's drafts folder; only a
  single matching document counts as success, and nothing is ever resent
- **The HTTP route is read-only by default**: `HttpEipClient` blocks
  `post/put/patch/delete` outright; changing state requires passing
  `read_only=False` explicitly
- **Logs are always masked**: Authorization and Cookie are never recorded; POST
  logging keeps field names and lengths, never values
- **Connection self-recovery**: a hung CDP connection restarts the browser and
  retries once — only once. Still failing after a restart means the problem is not
  the browser, and further retries would only delay someone noticing

## Layout

```
src/
  config.py          # central config, loads .env (all hostnames derived from EIP_URL)
  browser.py         # VPN check, launch debug Edge, CDP attach
  eip_client.py      # navigate EIP, open/close the trip form
  trip_form.py       # fill in, add traveler, send, verify the result
  duplicate_check.py # query the draft folder to prevent duplicate submissions
  session.py         # sign-in state detection
  state_machine.py   # flow state machine (SESSION_EXPIRED is a hard stop)
  dialog_handler.py  # classified dialog handling
  network_log.py     # network logging, with masking
  main.py            # interactive CLI entry point (trip registration)
  punch_form.py      # fill in, send and verify the missed-punch form
  punch_main.py      # interactive CLI entry point (missed punch)

  http_eip_client.py # pure HTTP + SSPI route (read-only by default)
  webforms_state.py  # ASP.NET WebForms form parsing (successful-controls rules)
  http_trip_form.py  # build the POST payload in memory (never sends it)

scripts/             # research and diagnostic POCs (mostly read-only)
docs/                # the full investigation and verification record
tests/               # 144 unit tests
```

## Tests

```powershell
python -m pytest tests/ -q
```

The tests need no connection to a real system.

## License and disclaimer

This tool was built against the observed behaviour of one specific EIP
deployment; other environments may be structured differently. Verify before use,
and understand that submitting is irreversible.
