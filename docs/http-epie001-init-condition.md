# What actually switches EPIE001 between its slim and full responses

**Conclusion**: the trigger is **whether the same session has GETted
`CollectData.aspx`**. With it → the full version (~91.7 KB, containing
`framePlus` / `ESSF21.aspx` / `Identifier` / `hdnplusFrameUrl`); without it → the
slim version (15,275 bytes, none of those four markers).

**Referer is ruled out**, and `platform.aspx` is not required either — the
successful group (S2) had neither.

Script: `scripts/http_epie001_init_ab_test.py` (GET only; no file under `src/` was
modified).
Raw data: `logs/http_epie001_init_ab_test/` (gitignored).

---

## Where the URLs came from (no guessing, but the provenance matters)

One thing to be honest about first: `logs/browser_capture/sequence.json` does
**not** contain the frameset load sequence from before the click — that recording
attached only just before the click, by which time the outer frames had long since
loaded, so the capture's very first event is EPIE001 itself. The initialization
URLs therefore cannot have been derived from the capture. Their actual provenance:

| Data | Source |
|---|---|
| The Referer value `…/FrameSet/platform.aspx` | `logs/browser_capture/sequence.json` seq=1 — a real captured value the browser actually sent |
| The individual initialization ASPX URLs | The real frame table in section 1 of `docs/eip-analysis.md` (observed in a real signed-in session) |
| **`CollectData.aspx`** | `logs/http_explorer/findings.json` step2 — the `/EFNET/` homepage's frame src is in fact `CollectData.aspx`, which forwards to `TreeMainFrame.aspx` |

`CollectData.aspx` is this round's key clue, and it had been overlooked all along:
every earlier failing probe hit **`TreeMainFrame.aspx` directly**, skipping
`CollectData.aspx`.

---

## Test design

As you asked, a cumulative fresh-session ladder: every rung is a **brand-new
`requests.Session()`** that re-authenticates via SSPI and **hits EPIE001 exactly
once, at the end** — never twice within one session, since GETting EPIE001 may
itself change server state.

## Round 1: the ascending ladder

| Rung | Initialization sequence | EPIE001 result | Bytes | sha256[:12] | Elapsed |
|---|---|---|---|---|---|
| S0 | homepage | **SLIM** | 15,275 | `cc52546a88ab` | 765ms |
| S1 | homepage → TreeMainFrame (direct, skipping CollectData) | **SLIM** | 15,275 | `cc52546a88ab` | 203ms |
| S2 | homepage → **CollectData** (which forwards to TreeMainFrame) | **FULL** ✅ | 91,702 | `e614ad664fd3` | 3,687ms |

After S2 succeeded the ladder stopped as instructed. S3-S7 (including the
browser-like full initialization and the two Referer groups) were **never run**,
because they were no longer needed: the minimal successful combination is just two
steps — homepage plus CollectData.

## An interlude: transient blocking (recorded as it happened)

During the first interleaved confirmation, S2 **timed out three times in a row**
(20s limit) while S0/S1 kept returning the slim version instantly. Since the first
success had taken only 3,687ms, 20s was not "just barely short", so I ran **one**
bounded probe (a single GET, 90s limit) to distinguish "slower" from "stuck" — and
it returned the full version, 91,698 bytes, **in 0.4 seconds**.

So those three were **transient blocking, not systematic failure**. It also led me
to raise the measurement tool's timeout from 20s to 60s (with the reason recorded
in a code comment), because the slim version always comes back instantly and
byte-identical, and mistaking "temporarily stuck" for "the server deliberately
served slim" would produce entirely wrong conclusions.

**The transient blocking itself is still unexplained** — the one anomaly still
outstanding (see question 6).

## Round 2: interleaved confirmation (deliberately starting from S2, to rule out time-of-day effects)

| # | Rung | Walked CollectData | Result | Bytes | sha256[:12] |
|---|---|---|---|---|---|
| 1 | S2 | ✅ | **FULL** | 91,698 | `de2a4df35eaa` |
| 2 | S0 | ❌ | SLIM | 15,275 | `cc52546a88ab` |
| 3 | S2 | ✅ | **FULL** | 91,698 | `026e05609f95` |
| 4 | S1 | ❌ | SLIM | 15,275 | `cc52546a88ab` |
| 5 | S2 | ✅ | **FULL** | 91,698 | `28e4e4d8f993` |

**Verdict: `CONFIRMED_COLLECTDATA_IS_THE_TRIGGER`**

Two details make this conclusion especially strong:

1. **S0/S1's hashes are identical every time** (`cc52546a88ab`) — the slim version
   is one and the same byte-identical response, not a random "sometimes more,
   sometimes less" result.
2. **S2's three hashes all differ** (all 91,698 bytes long, but different content)
   — because each contains a **brand-new Identifier**. That is exactly the expected
   behaviour, and it incidentally proves every GET really does generate a new
   Identifier.

Cumulative tally: **S2 returned the full version 5/5 whenever the server responded
at all** (the ascending run + the 90s probe + three interleaved runs), and
**S0/S1 returned slim 4/4**. Shuffling the order deliberately did not change the
pattern, so time-of-day effects are ruled out.

---

## Answers to your six questions

**1. Which initialization step flips EPIE001 from slim to full?**
**`CollectData.aspx`**, and it alone. The minimal successful combination is three
requests: GET `/EFNET/` → GET `CollectData.aspx` → GET
`EPIE001.aspx?FormID=ESSF21`. None of tree, Marquee, ShowStatus, titlebar1,
platform, main or HomeTab is needed.

**2. At which step is ASP.NET_SessionId created?**
**By whichever ASPX request comes first in that session — it belongs to no
particular step.** All three cases were observed: in S0 EPIE001 created it, in S1
TreeMainFrame, in S2 CollectData. (The `/EFNET/` homepage itself is static HTML and
creates none.)

**A key inference: the presence of a SessionId is not the trigger.** S1 clearly had
one, and EPIE001 still served slim. So what `CollectData.aspx` really establishes
is **some application-level state inside the session**, not merely "a session
exists".

**3. Is platform.aspx required?**
**No.** S2 never touched `platform.aspx` and got the full version 5/5.

**4. Could Referer=platform.aspx be a prerequisite?**
**No — ruled out.** S2's EPIE001 request **carried no Referer at all** and got the
full version 5/5. Your originally planned Experiment 4 (separating "initialization
sequence" from "Referer") already has its answer: **A, the initialization GET
sequence** — and no extra experiment is needed, because S2 is itself a clean
control for "initialized, no Referer". This also explains why the previous round in
`docs/http-essf21-referer-ab-test.md` came out INCONCLUSIVE: all six of those
sessions hit EPIE001 directly, and not one walked CollectData.

**5. Can requests now reproduce the browser's initialization?**
**At the EPIE001 layer: yes, and reproducibly (5/5).** And far more simply than
guessed — no need to replay the whole frameset, just one extra `CollectData.aspx`
request.

The ESSF21 layer is still unknown, because per your instruction **ESSF21 was not
GETted** this round.

**6. Is the "user-level single tab lock" hypothesis still needed?**
**As an explanation for slim vs full: no, it is superseded.** That phenomenon is
fully explained by whether CollectData was walked, with nothing to do with a
cross-session user-level lock — the evidence being that interleaved runs in the
same time window had S2 succeeding consistently and S0/S1 failing consistently.

**But do not discard it entirely**: those three consecutive timeouts really
happened and remain unexplained. Their shape (blocking rather than serving slim) is
unlike the lock originally imagined, yet it does look like some brief server-side
contention or locking. And it **may share a root cause with the earlier empty
ESSF21 body (Content-Length 0)** — both are "content that should be there and
isn't", and both appeared right after something had just succeeded. Worth keeping
an eye on, but there is no evidence yet, so it is not treated as a conclusion.

---

## Historical puzzles this clears up

Every "succeeded once, never again" record now lines up:

| Event | Walked CollectData? | Result |
|---|---|---|
| `http_eip_explorer.py`, first run | ✅ yes (the Step 2 frame crawl — `/EFNET/`'s frame src *is* CollectData) | full version + a real ESSF21 URL |
| `followup_probe.py` (hit TreeMainFrame directly) | ❌ skipped | failed |
| `followup_probe2.py` (hit EPIE001 directly ×4) | ❌ skipped | all 4 failed |
| Referer A/B test (6 sessions hitting EPIE001 directly) | ❌ all skipped | slim all 6 times |
| A real browser click | ✅ yes (loading the frameset necessarily walks it) | succeeded |

**Perfectly consistent, no exceptions.** Not luck — a required step that was always
there and simply had not been noticed.

---

## Current status

Per your stop conditions: the full EPIE001 has been obtained, and **ESSF21 was not
GETted**; no POST was issued, `btClosejQTab` was not called, the production
Playwright flow was not modified, and Phase 3 was not entered.

If this continues, the natural smallest next experiment is: **inside one session
that has walked CollectData, obtain a fresh Identifier and immediately GET ESSF21
once**, to see whether the earlier Content-Length 0 also stemmed from missing
CollectData initialization. That needs your approval (it would really GET ESSF21)
and will not be run unprompted.
