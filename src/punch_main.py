"""Interactive CLI for the missed-punch (ESSF03 補刷卡申請) form.

Usage:
    python src/punch_main.py

Same shape as src/main.py: collect the details, confirm once, check the
server for an existing form on that date, fill the live form, read the
values back off the page, and only click the real Send button after a
SECOND, final `y`. Sending is irreversible and is never retried.
"""
from main import confirm_on_server  # noqa: F401 - also sets up UTF-8 stdio, sys.path and .env

from playwright.sync_api import sync_playwright

import browser
import duplicate_check
import eip_client
import punch_form
from dialog_handler import UnexpectedDialogError
from punch_form import PunchRequest, PunchValidationError
from session import SessionState, wait_until_authenticated
from trip_form import SubmissionResult


def collect_punch_request() -> PunchRequest:
    print("Enter the missed-punch details:\n")
    while True:
        date = input("Date (e.g. 2026/10/16): ").strip()
        times = [t.strip() for t in input("Times, comma-separated (e.g. 08:30 or 08:30,18:00): ").split(",")
                 if t.strip()]
        print(f"Reason options: {' / '.join(punch_form.REASONS)}")
        reason = input("Reason [忘記刷卡]: ").strip() or "忘記刷卡"
        note = input("Note (optional): ").strip()
        req = PunchRequest(date=date, times=times, reason=reason, note=note)
        try:
            req.validate()
            return req
        except PunchValidationError as e:
            print(f"\n[error] {e}. Please re-enter.\n")


def show_confirmation(req: PunchRequest) -> bool:
    print("\n====================")
    print("Missed punch - confirm")
    print("====================")
    print(f"Date   : {req.date}")
    print(f"Times  : {', '.join(req.times)}")
    print(f"Reason : {req.reason}")
    print(f"Note   : {req.note}")
    print()
    return input("Proceed? [y/N] ").strip().lower() == "y"


def final_submit_confirmation(actual: dict) -> bool:
    print("\n==========================")
    print("Form filled. Values read back from the live page:")
    print("==========================")
    print(f"Date   : {actual.get(punch_form.DATE_FIELD_IDS[0])}")
    print(f"Times  : {', '.join(v for v in (actual.get(f) for f in punch_form.TIME_FIELD_IDS) if v)}")
    print(f"Reason : {actual.get(punch_form.REASON_FIELD_ID)}")
    print(f"Note   : {actual.get(punch_form.NOTE_FIELD_ID)}")
    print()
    print("Next step clicks the real Send button in EIP. This files the form\n"
          "into the approval workflow and cannot be undone.")
    return input("Final confirmation - really send? [y/N] ").strip().lower() == "y"


def main():
    req = collect_punch_request()
    if not show_confirmation(req):
        print("\nCancelled. Nothing was sent.")
        return

    print("\nChecking the server for an existing missed-punch form on that date...")
    # Before the browser logs in - see main.py: this lookup ends any
    # browser session already open.
    pattern = duplicate_check.punch_row_pattern(req.date)
    existing = duplicate_check.find_rows_via_http(pattern)
    if existing is None:
        print("\n[error] Could not query the drafts folder, so a duplicate cannot be "
              "ruled out. Stopped without sending.")
        return
    if existing:
        print("\n[error] There is already a missed-punch form for that date. "
              "Stopped without sending:")
        for row in existing:
            print(f"  - {row['docNumber']}: {row['text']}")
        return

    print(f"\nStarting a freshly logged-in Edge (CDP: {browser.CDP_URL})...")
    with sync_playwright() as pw:
        try:
            br, context = browser.attach_context(pw, fresh_session=True)
        except browser.CdpConnectionError as e:
            print(f"\n[error] {e}")
            return

        sent = False
        try:
            page = eip_client.open_homepage(context)
            state = wait_until_authenticated(page, timeout_ms=60000)
            if state != SessionState.AUTHENTICATED:
                print(f"\n[error] The EIP tab reports session state {state.value}, "
                      "not authenticated. Stopped without sending.")
                return

            frame = punch_form.open_form(page)
            punch_form.fill_form(page, frame, req)
            actual = punch_form.read_back(frame)
            bad = punch_form.mismatches(req, actual)
            if bad:
                print("\n[error] The form does not read back as entered. Stopped without sending:")
                for fid, (want, got) in bad.items():
                    print(f"  - {fid}: expected {want!r}, page shows {got!r}")
                return

            if not final_submit_confirmation(actual):
                print("\nFinal send cancelled. The Send button was never clicked.")
                return

            sent = True
            punch_form.submit_form(page)
            result, detail = punch_form.verify_submission(page)
            if result == SubmissionResult.UNKNOWN:
                result, detail = confirm_on_server(pattern, result, detail)
            if result == SubmissionResult.SUCCESS:
                print(f"\nMissed-punch form sent successfully. {detail}")
            else:
                print(f"\n[error] Send result: {result.value}. {detail}")
                print("Do not simply run the send again - confirm the real state via "
                      "form tracking first.")
        except (PunchValidationError, UnexpectedDialogError) as e:
            print(f"\n[error] {e}")
            if sent:
                print("This happened AFTER the Send click - check form tracking. Do not resend.")
        except Exception as e:  # noqa: BLE001 - last resort, still report state
            if sent:
                print(f"\n[error] Unexpected error AFTER the Send click: {e}\n"
                      "Whether it was filed is unknown - check form tracking. Do not resend.")
            else:
                print(f"\n[error] Unexpected error; stopped without sending: {e}")


if __name__ == "__main__":
    main()
