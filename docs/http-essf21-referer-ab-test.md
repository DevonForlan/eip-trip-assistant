# ESSF21 Referer A/B test: results

> **⚠️ Later update (parts of this superseded by `docs/http-epie001-init-condition.md`)**
> The hypothesis here — "a user may only have one in-creation ESSF21 tab" — **has
> been disproven**. The real cause is that none of these 6 sessions had **ever
> GETted `CollectData.aspx`**, the initialization step EPIE001 requires before it
> returns the full version. **Referer has also been ruled out** (requests without a
> Referer that did walk CollectData succeeded 5/5). The content below is kept as
> the record of what was observed at the time; for conclusions, defer to the newer
> document.

**Goal**: determine whether the Referer header is a prerequisite for `requests` +
SSPI to obtain ESSF21.aspx's real content. Six completely independent
`requests.Session()` runs (A×3 without Referer, B×3 with), each re-authenticating
via SSPI and walking EFNET → EPIE001 → ESSF21 afresh, so no Identifier is ever
shared. GET only; no POST anywhere (verifiable in the script with
`grep "\.post("`).

**Result up front: this test never reached the stage where Referer could actually
be compared.** All six independent sessions got stuck at Step 2 (GET
`EPIE001.aspx?FormID=ESSF21`) — consistently **15,275 bytes**, with no `<frame>`
tag pointing at ESSF21.aspx, exactly matching the "slim" response observed in
`docs/http-webforms-poc.md`. Since the ESSF21 URL was never obtained, neither group
ever issued a GET ESSF21 request whose Referer presence could be compared.

---

## Results

| Run | Referer | EPIE001 status | EPIE001 bytes | ESSF21 URL | HTTP | Body bytes | ESSCCDJ024 | VIEWSTATE | Identifier hash | Delay ms |
|---|---|---|---|---|---|---|---|---|---|---|
| A1 | no | 200 | 15,275 | not obtained | — | — | — | — | — | — |
| B1 | yes | 200 | 15,275 | not obtained | — | — | — | — | — | — |
| A2 | no | 200 | 15,275 | not obtained | — | — | — | — | — | — |
| B2 | yes | 200 | 15,275 | not obtained | — | — | — | — | — | — |
| A3 | no | 200 | 15,275 | not obtained | — | — | — | — | — | — |
| B3 | yes | 200 | 15,275 | not obtained | — | — | — | — | — | — |

All six `EPIE001 bytes` figures are identical (15,275) — not random variation but
the same "slim" response, stably reproduced. Because no ESSF21 URL was obtained,
there was no opportunity to capture an Identifier, hash it, or measure the
EPIE001→ESSF21 delay; those columns are honestly marked "not obtained" rather than
simply omitted.

---

## Verdict: INCONCLUSIVE (per your criteria)

Against the criteria you set, this result falls into none of the clean categories:

- Not "A repeatedly 200+0 bytes, B repeatedly 200+144KB" (neither group even
  reached ESSF21)
- Not "both A and B succeed"
- Not quite your anticipated "both A and B fail" either — the failure you had in
  mind was "both reach ESSF21 and both get an empty 200", whereas what actually
  happened is that **neither group got as far as ESSF21**, stalling earlier at the
  EPIE001 stage.

**Per your instruction: marked INCONCLUSIVE, not proceeding to Phase 3.**

---

## What this means: a new, stronger hypothesis

**Referer was not disproven here — it never got its turn.** What is genuinely
notable is that **six fully independent HTTP calls, sharing no cookie or session,
all produced an identical slim response**. That strongly suggests the blocker has
**nothing to do with per-connection things like HTTP session, cookies or Referer**,
and is instead some server-side state **bound to the signed-in identity and
persisting across connections**.

Stringing all the observations together, the most plausible chronological reading:

1. The very first `http_eip_explorer.py` run succeeded once (full EPIE001, a real
   ESSF21 URL).
2. From then on, every subsequent `requests` call that day got the slim version —
   including these six brand-new sessions.
3. In between, though, a **real browser** click on the trip shortcut made EPIE001
   succeed once more (with another brand-new Identifier), and ESSF21 really did
   return 144,494 bytes of content.
4. This run (after the browser's success) is back to slim every time.

That pattern fits the hypothesis "**a single user — not a single session or cookie
— may only have one 'in-creation' ESSF21 tab; once any attempt (browser or
requests) creates one successfully, every later attempt gets the slim version until
that tab is closed or times out**" rather well. It is the most explanatory theory
so far, but it is **not directly confirmed**, because no direct test — deliberately
triggering a tab close and immediately retrying — has been run.

You had in fact already anticipated this in "smallest next experiment (c)" in
`docs/http-webforms-poc.md` (test calling the close-tab backend logic), and these
results make the hypothesis more credible. But **calling the close-tab function is
still on your "not for now" list, so it was not run here and will not be run
unprompted.**

---

## Answers to the six questions

**1. Is Referer a prerequisite?**
Undetermined — this sample never reached the point where Referer could be compared.
Both groups stopped, for the same reason (EPIE001 returning slim), before the one
meaningful difference between them came into play, so the question stays open.

**2. Can pure HTTP now obtain ESSF21 reliably?**
No. All six runs failed, at a stage earlier than obtaining ESSF21's content. The
cumulative record so far: the full EPIE001 has been obtained twice (once over pure
HTTP, once by a real browser, and in the browser's case ESSF21 itself was obtained
too) against many failures. Nowhere near reliable.

**3. Does the Identifier look single-use?**
No new evidence from this run (no new Identifier was obtained). The previous
report's status stands: not ruled out, but not the only plausible explanation
either. "One in-creation tab per user" now looks more explanatory than
"single-use Identifier", because it also explains why the response is the slim
version rather than an empty 200, and why it repeats identically many times over
instead of varying randomly.

**4. Is the ASP.NET session stable?**
Stable, but it did not help here. All six sessions completed SSPI authentication
cleanly, all got 200s, all conversed normally (`efnet_status` /
`epie001_status` all 200, with zero authentication failures or connection
timeouts). The problem is not "cannot connect" or "authentication failed": the
connection worked, authentication passed, and the application logic served the slim
content.

**5. Does this meet the Phase 2 success criteria?**
No. Phase 2's original criterion was "obtain ESSF21's real content over pure HTTP
and parse out the fields". Not only was that not met, but even the intermediate
milestone reached once before — obtaining the ESSF21 URL with a real Identifier —
could not be reproduced in any of the six runs.

**6. Next: Phase 3, or more header/state analysis?**
Neither, for now. Both presuppose being able to reach ESSF21 reliably, and this run
shows that even the step before it (EPIE001 returning the full version) cannot be
reproduced reliably. **What deserves priority is understanding what actually
switches EPIE001 between its slim and full responses** — a more upstream and more
consequential question than Referer. The reasonable smallest next experiment (not
run here, awaiting your direction): **confirm whether this user really does have an
"in-creation" ESSF21 tab still open** — e.g. via the document-tracking query logic
already validated in `duplicate_check.py`, or simply by having you check the tab
state in the real Edge window — rather than rushing to guess at a close-tab backend
call.

---

## Technical debt (recorded, not fixed here, deliberately not mixed into this A/B test)

1. **`scripts/capture_browser_sequence.py` reads frame content too early**: it
   calls `.content()` as soon as the frame URL appears, without waiting for
   `load`/`networkidle`, so the saved `essf21_response.html` is only 1,409 bytes (a
   mid-render intermediate state), inconsistent with the 144,494 bytes the network
   layer recorded. The fix is to follow `eip_client.open_trip_form()` and call
   `frame.wait_for_load_state()`, but that file is left alone here.
2. **A false positive in `browser.py`'s health check**: the CDP `/json` metadata
   endpoint that `_eip_tab_has_started_loading()` reads sometimes reports a `url`
   that disagrees with what Playwright sees via `page.url`. Witnessed once
   directly: `/json` said `http://eip.example.com/EFNET/` while the actual tab was
   on `chrome-error://chromewebdata/`. So the signal `ensure_debug_edge()` uses to
   decide "sign-in succeeded" may itself be unreliable, independent of how many
   times it retries. `browser.py` is not modified here.

Both are recorded only, to be discussed together whenever you decide to tackle
sign-in stability.

---

## Current status

The Referer A/B test is complete and marked INCONCLUSIVE. Stopping here as
instructed: no Phase 3, no POST, no close-tab call, and no changes to
`capture_browser_sequence.py` or `browser.py`. Awaiting your next instruction.
