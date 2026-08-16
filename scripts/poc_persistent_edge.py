"""POC (read-only, does NOT touch the working automation) - can Playwright's
own launch_persistent_context(channel="msedge") reach EIP without hitting
the NTLM CDP-block that connect_over_cdp() / bundled Chromium hit?

This is a research question, not a replacement: if this works, it would
mean Playwright can drive real Edge directly (full Playwright protocol
fidelity, no CDP-attach quirks, proper dialog handling) instead of the
current attach-to-an-externally-launched-Edge workaround in src/browser.py.

This script:
  1. Launches real Microsoft Edge (channel="msedge") via Playwright itself,
     with a dedicated persistent profile (separate from .edge-profile,
     so it never collides with or corrupts the working setup).
  2. Navigates to the EIP URL via normal page.goto() (this IS a
     CDP-driven navigation, on purpose - that's exactly the case we're
     testing).
  3. Reports whether it hit ERR_INVALID_AUTH_CREDENTIALS or actually
     logged in.
  4. Does NOT click anything, does NOT fill any form, does NOT submit.

Usage:
    python scripts/poc_persistent_edge.py

Prerequisite: VPN must be connected (see scripts/ensure_vpn.py).
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

import os  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

EIP_URL = os.environ.get("EIP_URL", "http://eip.example.com/EFNET/")
POC_PROFILE_DIR = ROOT / ".poc-persistent-edge-profile"


def main():
    POC_PROFILE_DIR.mkdir(exist_ok=True)
    print(f"啟動真正的 Microsoft Edge（Playwright launch_persistent_context, channel=msedge）")
    print(f"profile: {POC_PROFILE_DIR}")
    print(f"目標: {EIP_URL}\n")

    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(POC_PROFILE_DIR),
            channel="msedge",
            headless=False,
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            page.goto(EIP_URL, wait_until="domcontentloaded", timeout=20000)
            print(f"[結果] goto() 成功，沒有拋出例外")
            print(f"  最終 URL: {page.url}")
            print(f"  Title: {page.title()}")
            if "電子簽核" in page.title() or page.url.rstrip("/").endswith("EFNET"):
                print("  => 看起來已經是登入後的畫面（需要你親眼確認截圖）")
            page.screenshot(path=str(ROOT / "screenshots" / "poc_persistent_edge_result.png"))
            print(f"  截圖已存到 screenshots/poc_persistent_edge_result.png")
        except Exception as e:  # noqa: BLE001 - this is exactly what we're testing for
            print(f"[結果] goto() 失敗：{type(e).__name__}: {e}")
            try:
                page.screenshot(path=str(ROOT / "screenshots" / "poc_persistent_edge_error.png"))
                print(f"  錯誤畫面截圖已存到 screenshots/poc_persistent_edge_error.png")
            except Exception:  # noqa: BLE001
                pass

        print("\n未點擊、未填寫、未送出任何內容。")
        context.close()


if __name__ == "__main__":
    main()
