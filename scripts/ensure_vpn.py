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
    print(f"Checking whether EIP ({browser.EIP_HOST}) is reachable...")
    if browser.is_eip_reachable():
        print("[ok] Reachable - no need to open FortiClient.")
        return

    print("[info] Not reachable - the VPN is probably down. Opening FortiClient...")
    print("Connect in the FortiClient window and complete the 2FA QR scan on your phone.")
    print("This will re-check every few seconds, for up to 3 minutes...")

    if browser.ensure_vpn_connected():
        print("[ok] Connected - you can now run scripts/inspect_eip.py or src/main.py.")
    else:
        print("[warn] Timed out and EIP is still unreachable. Check that FortiClient "
              "actually connected, or inspect the network by hand, then re-run this.")


if __name__ == "__main__":
    main()
