"""Interactive CLI entry point.

Usage:
    python src/main.py

Collects the trip details interactively, shows a confirmation summary,
and only proceeds to the browser automation step if the user types `y`.
After the form is filled in the live EIP page, it reads the values back
from the browser and asks for a SECOND, final `y` confirmation before
clicking the real Send button - that click is a genuine,
irreversible submission into the approval workflow.

2026-08 architecture review: the flow below is driven by an explicit
state machine (state_machine.TripFlow) instead of a bare sequence of
function calls. The one rule that overrides everything else: the
moment session.check_session() reports EXPIRED, the flow stops - no
step past that point is allowed to run, and nothing here will ever
auto-retry a send. A duplicate-submission check (duplicate_check) also
runs before every send attempt, since a FAILED or UNKNOWN result must
never be blindly retried without first confirming whether the earlier
attempt actually went through.

Requires a real, already-logged-in Edge window (see
scripts/inspect_eip.py or docs/eip-analysis.md for why EIP's Windows
Integrated Auth means a freshly-launched, unauthenticated browser
cannot be used here) - browser.attach_context() will try to get you
there automatically, falling back to printed manual instructions if it
can't.
"""
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Windows consoles often default stdin/stdout/stderr to a legacy codepage
# (e.g. cp950) that cannot round-trip every Chinese character typed in or
# read back from the browser - force UTF-8 on all three so the CLI never
# crashes on encoding.
if sys.stdin.encoding and sys.stdin.encoding.lower() != "utf-8":
    sys.stdin.reconfigure(encoding="utf-8")
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

load_dotenv(ROOT / ".env")

import browser  # noqa: E402
import duplicate_check  # noqa: E402
import eip_client  # noqa: E402
import trip_form  # noqa: E402
from dialog_handler import UnexpectedDialogError  # noqa: E402
from session import SessionState, check_session, wait_until_authenticated  # noqa: E402
from state_machine import SessionExpiredError, TripFlow, TripState  # noqa: E402
from trip_form import TravelerValidationError, TripRequest  # noqa: E402


def prompt(label: str) -> str:
    value = input(f"{label}: ").strip()
    while not value:
        value = input(f"{label} (required, please re-enter): ").strip()
    return value


def collect_trip_request() -> TripRequest:
    print("Enter the trip details:\n")
    date = prompt("Trip date")
    start_time = prompt("Start time")
    end_time = prompt("End time")
    location = prompt("Location")
    reason = prompt("Reason")
    transport = prompt("Transport")
    note = input("Note: ").strip()  # optional
    return TripRequest(
        date=date,
        start_time=start_time,
        end_time=end_time,
        location=location,
        reason=reason,
        transport=transport,
        note=note,
    )


def show_confirmation(trip: TripRequest) -> bool:
    print("\n====================")
    print("Trip application - confirm")
    print("====================")
    print(f"Date     : {trip.date}")
    print(f"Time     : {trip.start_time} - {trip.end_time}")
    print(f"Location : {trip.location}")
    print(f"Reason   : {trip.reason}")
    print(f"Transport: {trip.transport}")
    print(f"Note     : {trip.note}")
    print()
    print("(Note: this EIP form has no separate transport field, so transport is\n"
          " appended to the note field.)")
    print()
    answer = input("Proceed? [y/N] ").strip().lower()
    return answer == "y"


def final_submit_confirmation(page, traveler_name: str) -> bool:
    frame = eip_client.find_trip_form_frame(page)
    from trip_form import FIELD_IDS

    print("\n==========================")
    print("Form filled. Values read back from the live page:")
    print("==========================")
    print(f"Start date/time: {frame.input_value('#' + FIELD_IDS['start_date'])} "
          f"{frame.input_value('#' + FIELD_IDS['start_time'])}")
    print(f"End date/time  : {frame.input_value('#' + FIELD_IDS['end_date'])} "
          f"{frame.input_value('#' + FIELD_IDS['end_time'])}")
    print(f"Location       : {frame.input_value('#' + FIELD_IDS['location'])}")
    print(f"Reason         : {frame.input_value('#' + FIELD_IDS['reason'])}")
    print(f"Note           : {frame.input_value('#' + FIELD_IDS['note'])}")
    print(f"Traveler       : {traveler_name}")
    print()
    print("Next step clicks the real Send button in EIP. This files the application\n"
          "into the approval workflow and cannot be undone.")
    answer = input("Final confirmation - really send? [y/N] ").strip().lower()
    return answer == "y"


def _require_authenticated(page, flow: TripFlow, step_reason: str) -> None:
    """Check session health and transition the flow accordingly. Raises
    SessionExpiredError (via flow.transition) if the session is gone -
    callers should let that propagate all the way out to main()'s
    top-level handler rather than catching it locally, since there is
    nothing safe to do at any intermediate step except stop.

    Waits out an UNKNOWN rather than treating it as fatal: these checks run
    right after a postback, when the frameset is being rebuilt and briefly
    looks unrecognizable. EXPIRED still stops immediately.
    """
    state = wait_until_authenticated(page)
    if state == SessionState.EXPIRED:
        flow.transition(TripState.SESSION_EXPIRED, step_reason)  # raises
    elif state == SessionState.UNKNOWN:
        raise RuntimeError(
            f"Could not confirm the session is still valid (at: {step_reason}). "
            "Treating that as unsafe to continue - log in again and retry."
        )


def confirm_on_server(pattern, result, detail):
    """Settle an UNKNOWN send by asking the server. On this host a send
    that succeeded routinely ends on the logout page, which the browser
    can only report as UNKNOWN. Exactly one matching row is a success;
    anything else stays UNKNOWN for a human to look at. Never resends."""
    print("\nThe browser could not confirm the result; checking the drafts folder "
          "on the server (up to a minute)...")
    rows = duplicate_check.wait_for_rows_via_http(pattern)
    if rows and len(rows) == 1:
        return (trip_form.SubmissionResult.SUCCESS,
                f"Confirmed on the server: {rows[0]['docNumber']}")
    if rows:
        found = ", ".join(r["docNumber"] for r in rows)
        return result, f"{detail} | The server has SEVERAL matching documents: {found}"
    if rows is None:
        return result, f"{detail} | The drafts folder could not be queried either."
    return result, f"{detail} | No matching document appeared on the server within a minute."


def main():
    trip = collect_trip_request()
    confirmed = show_confirmation(trip)

    if not confirmed:
        print("\nCancelled. Nothing was sent.")
        return

    print("\nChecking the server for an existing document with the same date/time, "
          "to avoid a duplicate submission...")
    # Over HTTP, and before the browser logs in: each user gets a single EIP
    # session, so this lookup ends any browser session already open. Run any
    # later and the form it would be guarding dies under it.
    existing = duplicate_check.find_existing_submission_via_http(trip)
    if existing is None:
        print("\n[error] Could not query the drafts folder, so a duplicate cannot be "
              "ruled out. Stopped without sending.")
        return
    if existing:
        print("\n[error] Found what looks like a duplicate in the drafts folder. "
              "Stopped without sending:")
        for row in existing:
            print(f"  - {row['docNumber']}: {row['text']}")
        print("Check those documents first, then decide whether to resubmit "
              "with a different date/time.")
        return

    print(f"\nStarting a freshly logged-in Edge (CDP: {browser.CDP_URL})...")
    print("(EIP needs Windows Integrated Authentication, so this attaches to that\n"
          " browser rather than launching one through Playwright.)")

    flow = TripFlow()

    with sync_playwright() as pw:
        try:
            br, context = browser.attach_context(pw, fresh_session=True)
        except browser.CdpConnectionError as e:
            print(f"\n[error] {e}")
            return

        try:
            page = eip_client.open_homepage(context)

            # Wait rather than judge instantly: the frameset can still be
            # assembling here, which reads as UNKNOWN and would abort a
            # perfectly good session.
            session_state = wait_until_authenticated(page)
            if session_state != SessionState.AUTHENTICATED:
                print(f"\n[error] The EIP tab reports session state {session_state.value}, "
                      "not authenticated. Stopping.")
                if session_state == SessionState.EXPIRED:
                    print("Log back into EIP, then run this program again.")
                return
            flow.transition(TripState.AUTHENTICATED, "confirmed logged in")

            eip_client.open_trip_form(page)
            _require_authenticated(page, flow, "after opening the trip form")
            flow.transition(TripState.FORM_OPEN, "opened the trip form")

            trip_form.fill_form(page, trip)
            missing = trip_form.check_required_fields(page)
            if missing:
                flow.transition(TripState.FAILED, f"missing required fields: {', '.join(missing)}")
                print(f"\n[error] Missing required fields: {', '.join(missing)}. "
                      "Stopped without sending.")
                return
            flow.transition(TripState.FORM_FILLED, "filled the form")

            employee_code = trip_form.get_filler_employee_code(page)
            traveler_name = trip_form.add_traveler(page, employee_code)
            _require_authenticated(page, flow, "after saving the traveler detail")
            flow.transition(TripState.TRAVELER_SAVED, f"traveler added: {traveler_name}")

            if not final_submit_confirmation(page, traveler_name):
                print("\nFinal send cancelled. The form is left on screen; the Send "
                      "button was never clicked.")
                return
            flow.transition(TripState.READY_TO_SEND, "user gave final confirmation")

            flow.transition(TripState.SENDING, "clicking the Send button")
            trip_form.submit_form(page)

            result, detail = trip_form.verify_submission(page)
            if result == trip_form.SubmissionResult.UNKNOWN:
                result, detail = confirm_on_server(
                    duplicate_check.trip_row_pattern(trip), result, detail)
            if result == trip_form.SubmissionResult.SUCCESS:
                flow.transition(TripState.SENT, detail)
                print(f"\nTrip application sent successfully. {detail}")
            else:
                flow.transition(TripState.FAILED, detail)
                print(f"\n[error] Send result: {result.value}. {detail}")
                print("Do not simply run the send again - confirm the real state via "
                      "form tracking first.")
        except SessionExpiredError as e:
            print(f"\n[error] {e}")
        except (TravelerValidationError, UnexpectedDialogError) as e:
            print(f"\n[error] {e}")
        except Exception as e:  # noqa: BLE001 - last resort, still report state
            print(f"\n[error] Unexpected error; stopped without sending: {e}")
        finally:
            print(f"\nFlow history: {flow.history_summary() or '(no state entered)'}")
        # Deliberately not closing br/context here - it's your real,
        # manually-logged-in Edge window, not one this script launched.


if __name__ == "__main__":
    main()
