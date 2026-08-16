"""Check whether EIP is reachable, and if not, open FortiClient for you.

This does NOT touch your VPN credentials or 2FA in any way - it only:
  1. Checks whether the EIP hostname currently resolves (a quick, cheap
     proxy for "am I on the corporate network/VPN").
  2. If not, launches the FortiClient GUI so you can pick your VPN
     connection and complete it yourself (including scanning the 2FA QR
     code with your phone - that part cannot and should not be automated).
  3. Polls in the background until EIP becomes reachable (or a timeout),
     so you don't have to keep checking manually.

The actual logic lives in src/browser.py (ensure_vpn_connected) so that
src/main.py and scripts/inspect_eip.py can call the same check as part of
their normal startup instead of failing outright when VPN isn't up.

Usage:
    python scripts/ensure_vpn.py
"""
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env")

import browser  # noqa: E402


def main():
    print(f"檢查是否連得到 EIP（{browser.EIP_HOST}）...")
    if browser.is_eip_reachable():
        print("[ok] 已經連得到，不需要開 FortiClient。")
        return

    print("[info] 連不到，可能是 VPN 沒連上。正在開啟 FortiClient...")
    print("請在 FortiClient 視窗裡連線並用手機完成 QR code 驗證。")
    print("這裡會自動每幾秒檢查一次，最多等 3 分鐘...")

    if browser.ensure_vpn_connected():
        print("[ok] 已經連上了，可以繼續執行 scripts/inspect_eip.py 或 src/main.py 了。")
    else:
        print("[warn] 等太久還是連不到，請確認 FortiClient 是否已經連線成功，"
              "或手動檢查網路狀態後再重新執行本程式。")


if __name__ == "__main__":
    main()
