"""Interactive CLI entry point.

Usage:
    python src/main.py

Collects the trip details interactively, shows a confirmation summary,
and only proceeds to the browser automation step if the user types `y`.
After the form is filled in the live EIP page, it reads the values back
from the browser and asks for a SECOND, final `y` confirmation before
clicking the real "傳送" (Send) button - that click is a genuine,
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
    value = input(f"{label}：").strip()
    while not value:
        value = input(f"{label}（必填，請重新輸入）：").strip()
    return value


def collect_trip_request() -> TripRequest:
    print("請輸入出差申請資訊：\n")
    date = prompt("出差日期")
    start_time = prompt("開始時間")
    end_time = prompt("結束時間")
    location = prompt("出差地點")
    reason = prompt("出差事由")
    transport = prompt("交通方式")
    note = input("備註：").strip()  # optional
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
    print("出差申請確認")
    print("====================")
    print(f"日期：{trip.date}")
    print(f"時間：{trip.start_time} - {trip.end_time}")
    print(f"地點：{trip.location}")
    print(f"事由：{trip.reason}")
    print(f"交通方式：{trip.transport}")
    print(f"備註：{trip.note}")
    print()
    print("（提示：EIP 的出差登記表單沒有獨立的交通方式欄位，"
          "會併入「備註」欄位一起寫入）")
    print()
    answer = input("確認送出？ [y/N] ").strip().lower()
    return answer == "y"


def final_submit_confirmation(page, traveler_name: str) -> bool:
    frame = eip_client.find_trip_form_frame(page)
    from trip_form import FIELD_IDS

    print("\n==========================")
    print("表單已填入，讀回實際畫面內容：")
    print("==========================")
    print(f"開始日期/時間：{frame.input_value('#' + FIELD_IDS['start_date'])} "
          f"{frame.input_value('#' + FIELD_IDS['start_time'])}")
    print(f"結束日期/時間：{frame.input_value('#' + FIELD_IDS['end_date'])} "
          f"{frame.input_value('#' + FIELD_IDS['end_time'])}")
    print(f"出差地點：{frame.input_value('#' + FIELD_IDS['location'])}")
    print(f"出差原因：{frame.input_value('#' + FIELD_IDS['reason'])}")
    print(f"備註：{frame.input_value('#' + FIELD_IDS['note'])}")
    print(f"出差人：{traveler_name}")
    print()
    print("接下來會點擊 EIP 上真正的「傳送」按鈕，這是無法復原的正式送出動作。")
    answer = input("最終確認：真的要送出嗎？ [y/N] ").strip().lower()
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
            f"無法確認登入狀態是否還有效（於「{step_reason}」），"
            "為安全起見視同無法繼續，請重新登入後再試一次。"
        )


def main():
    trip = collect_trip_request()
    confirmed = show_confirmation(trip)

    if not confirmed:
        print("\n已取消，未執行任何送出動作。")
        return

    print(f"\n正在連線到已啟動並登入的 Edge（CDP: {browser.CDP_URL}）...")
    print("（EIP 需要 Windows 整合驗證，所以是連到你手動登入的 Edge，而非開新的瀏覽器）")

    flow = TripFlow()

    with sync_playwright() as pw:
        try:
            br, context = browser.attach_context(pw)
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
                print(f"\n[error] 目前 EIP 分頁的登入狀態是 {session_state.value}，不是已登入，已停止。")
                if session_state == SessionState.EXPIRED:
                    print("請重新登入 EIP 後再重新執行本程式。")
                return
            flow.transition(TripState.AUTHENTICATED, "確認已登入")

            eip_client.open_trip_form(page)
            _require_authenticated(page, flow, "開啟出差登記表單後")
            flow.transition(TripState.FORM_OPEN, "開啟出差登記表單")

            trip_form.fill_form(page, trip)
            missing = trip_form.check_required_fields(page)
            if missing:
                flow.transition(TripState.FAILED, f"必填欄位缺漏：{', '.join(missing)}")
                print(f"\n[error] 必填欄位缺漏：{', '.join(missing)}，已停止，未送出。")
                return
            flow.transition(TripState.FORM_FILLED, "填入表單資料")

            print("\n檢查「表單追蹤處理」是否已經有相同日期/時間的單據，避免重複送出...")
            # Checks the browser view AND an independent HTTP query - the
            # browser's list has been caught serving cached results, and a
            # missed duplicate means filing the same trip twice.
            existing = duplicate_check.find_existing_submission_anywhere(page, trip)
            if existing:
                flow.transition(TripState.FAILED, "偵測到可能重複的既有單據")
                print("\n[error] 在「原稿資料匣」找到疑似重複的單據，已停止，未送出：")
                for row in existing:
                    print(f"  - 單號 {row['docNumber']}：{row['text']}")
                print("請先確認這些單據的狀態，再決定是否要用其他日期/時間重新送出。")
                return

            # Checking 表單追蹤處理 switches the sidebar and backgrounds
            # the 出差登記 tab (its content becomes hidden, not just
            # unfocused) - bring it back before touching the form again.
            eip_client.reactivate_trip_form_tab(page)

            employee_code = trip_form.get_filler_employee_code(page)
            traveler_name = trip_form.add_traveler(page, employee_code)
            _require_authenticated(page, flow, "儲存出差人明細後")
            flow.transition(TripState.TRAVELER_SAVED, f"已加入出差人：{traveler_name}")

            if not final_submit_confirmation(page, traveler_name):
                print("\n已取消最終送出，表單內容仍留在畫面上，未呼叫送出按鈕。")
                return
            flow.transition(TripState.READY_TO_SEND, "使用者最終確認送出")

            flow.transition(TripState.SENDING, "點擊傳送按鈕")
            trip_form.submit_form(page)

            result, detail = trip_form.verify_submission(page)
            if result == trip_form.SubmissionResult.SUCCESS:
                flow.transition(TripState.SENT, detail)
                print(f"\n已送出出差登記申請成功。{detail}")
            else:
                flow.transition(TripState.FAILED, detail)
                print(f"\n[error] 送出結果：{result.value}。{detail}")
                print("切勿直接重新執行送出 - 請先用「表單追蹤處理」確認實際狀態。")
        except SessionExpiredError as e:
            print(f"\n[error] {e}")
        except (TravelerValidationError, UnexpectedDialogError) as e:
            print(f"\n[error] {e}")
        except Exception as e:  # noqa: BLE001 - last resort, still report state
            print(f"\n[error] 執行過程發生未預期錯誤，已停止，未送出：{e}")
        finally:
            print(f"\n本次流程狀態記錄：{flow.history_summary() or '(尚未進入任何狀態)'}")
        # Deliberately not closing br/context here - it's your real,
        # manually-logged-in Edge window, not one this script launched.


if __name__ == "__main__":
    main()
