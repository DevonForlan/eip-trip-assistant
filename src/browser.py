"""Browser / VPN / session helpers shared by exploration and automation scripts.

EIP requires Windows Integrated Authentication (NTLM/Negotiate). Playwright
cannot complete that handshake through its own navigation calls -
CDP-driven navigation (Page.goto(), context.new_page().goto(), ...) is
deliberately excluded from Chromium's automatic NTLM SSO, for the same
reason a malicious script shouldn't be able to silently borrow your Windows
identity against an internal server.

Launching the browser with the target URL as a *command-line argument*
is not CDP-driven, though, so SSO can complete for it. So the flow here
is: make sure VPN is up, launch (or reuse) a dedicated debug-enabled Edge
with the EIP URL as a launch argument, then attach Playwright to it purely
to read/fill the DOM afterwards - never to navigate.

That launch also needs --auth-server-allowlist. This dedicated profile
does not inherit whatever makes the user's everyday Edge log in silently,
so without the flag Chromium refuses to send Windows credentials
automatically and pops a native "Windows 安全性" credential dialog
instead. Nobody answers that dialog in an automated run, the request ends
up unauthenticated, and the tab lands on chrome-error://chromewebdata/ -
which for a long time was misdiagnosed here as flaky NTLM negotiation
(see docs/login-automation-investigation.md, whose conclusions on that
point are superseded). With the flag, login is silent and immediate.

Note the flag was tried much earlier and dismissed as useless, but that
test was against a *different* problem - a Playwright-driven page.goto(),
which is blocked regardless of any allowlist. The two are unrelated.
"""
import json
import socket
import subprocess
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Playwright

from config import (  # noqa: F401 - re-exported for existing callers/tests
    AUTH_SERVER_ALLOWLIST,
    CDP_URL,
    EDGE_EXE,
    EDGE_PROFILE_DIR,
    EIP_HOST,
    EIP_URL,
    FORTICLIENT_PATH,
    ROOT,
)


def edge_launch_args(url: str) -> list:
    """The exact argv used to launch the debug Edge. Shared so the manual
    fallback instructions can never drift from what the code actually runs.

    Kept as a list rather than a formatted string on purpose: the profile
    path can contain spaces (e.g. a synced "OneDrive - Company" folder),
    and passing it
    through anything that splits on whitespace silently truncates it -
    which once caused Edge to treat the tail as a URL and write a whole
    browser profile into an unintended directory.
    """
    return [
        EDGE_EXE,
        "--remote-debugging-port=9222",
        f"--user-data-dir={EDGE_PROFILE_DIR}",
        "--no-first-run",
        f"--auth-server-allowlist={AUTH_SERVER_ALLOWLIST}",
        url,
    ]


class CdpConnectionError(RuntimeError):
    pass


class VpnRequiredError(CdpConnectionError):
    """Raised when EIP is unreachable and waiting for VPN timed out.

    Subclasses CdpConnectionError so existing `except CdpConnectionError`
    call sites handle this the same way without extra changes.
    """


def is_eip_reachable(timeout: float = 3.0) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.gethostbyname(EIP_HOST)
        return True
    except OSError:
        return False


def _cdp_port_is_up(timeout: float = 1.0) -> bool:
    try:
        urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=timeout)
        return True
    except Exception:  # noqa: BLE001 - any failure just means "not up yet"
        return False


def _eip_tab_has_started_loading(timeout: float = 1.0) -> bool:
    """True once one of the open tabs' URL contains the EIP host. Right
    after launch, the CDP port can accept connections before the tab we
    passed as a launch argument has actually started navigating there -
    without this check, callers can race ahead and find no matching page,
    then fall back to a Playwright-driven goto() that hits the NTLM wall
    this whole launch-as-argument trick exists to avoid."""
    try:
        with urllib.request.urlopen(f"{CDP_URL}/json", timeout=timeout) as resp:
            targets = json.loads(resp.read())
    except Exception:  # noqa: BLE001
        return False
    return any(EIP_HOST in t.get("url", "") for t in targets if t.get("type") == "page")


def launch_forticlient() -> bool:
    if not Path(FORTICLIENT_PATH).exists():
        return False
    subprocess.Popen([FORTICLIENT_PATH])
    return True


def ensure_vpn_connected(timeout_seconds: int = 180, poll_seconds: int = 3) -> bool:
    """Check EIP is reachable; if not, open FortiClient and wait for you to
    connect - including scanning the 2FA QR code with your phone yourself,
    which can't and shouldn't be automated. Returns True once reachable,
    False if it timed out.
    """
    if is_eip_reachable():
        return True

    launch_forticlient()

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_eip_reachable():
            return True
        time.sleep(poll_seconds)
    return False


def _pid_listening_on_port(port: int) -> int | None:
    try:
        out = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=5
        ).stdout
    except Exception:  # noqa: BLE001
        return None
    for line in out.splitlines():
        if f":{port} " in line and "LISTENING" in line:
            parts = line.split()
            try:
                return int(parts[-1])
            except ValueError:
                continue
    return None


def _kill_debug_edge() -> None:
    """Kill whatever is listening on the debug port. Only ever targets
    our own dedicated debug-profile Edge instance (identified purely by
    which process owns port 9222) - never the user's real browser
    windows, which don't have --remote-debugging-port at all."""
    pid = _pid_listening_on_port(9222)
    if pid is not None:
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)


def _launch_debug_edge_once(url: str, settle_timeout_seconds: int) -> bool:
    """Single launch attempt. Returns True if the tab settles on the real
    EIP URL for a couple of consecutive checks, False on timeout.

    Empirically, the tab often flickers through a transient
    chrome-error:// state (DNS/NTLM retry) before settling on the real
    EIP URL, so a single "does the URL match yet" check is not enough -
    this waits for that match to hold for a couple of consecutive checks,
    otherwise a caller can race ahead against a tab that flips back to an
    error page a moment later.
    """
    if not _cdp_port_is_up():
        EDGE_PROFILE_DIR.mkdir(exist_ok=True)
        subprocess.Popen(edge_launch_args(url))

    deadline = time.time() + settle_timeout_seconds
    consecutive_ok = 0
    while time.time() < deadline:
        if _cdp_port_is_up() and _eip_tab_has_started_loading():
            consecutive_ok += 1
            if consecutive_ok >= 2:
                return True
        else:
            consecutive_ok = 0
        time.sleep(1)
    return False


def ensure_debug_edge(url: str = EIP_URL, attempts: int = 3, settle_timeout_seconds: int = 25) -> None:
    """Make sure a debug-enabled Edge is running, launching it pointed at
    `url` if it isn't. Launching with the URL as a command-line argument
    (instead of navigating to it after the fact) is what lets Windows NTLM
    SSO complete automatically - see module docstring.

    A single launch can get stuck in a transient chrome-error retry loop
    that never resolves on its own (observed empirically - waiting longer
    within the same launch doesn't help). A full kill + relaunch cycle
    reliably gives it a fresh attempt, so this retries up to `attempts`
    times rather than just waiting once with a long timeout.
    """
    if not Path(EDGE_EXE).exists():
        raise CdpConnectionError(f"找不到 Edge：{EDGE_EXE}。請設定環境變數 EIP_EDGE_PATH。")

    for attempt in range(1, attempts + 1):
        if _launch_debug_edge_once(url, settle_timeout_seconds):
            return
        if attempt < attempts:
            _kill_debug_edge()
            time.sleep(1)

    raise CdpConnectionError(
        f"啟動 Edge 逾時（已重試 {attempts} 次，可能一直卡在 NTLM/DNS 重試），請確認網路狀態。"
    )


def attach_context(playwright: Playwright) -> tuple[Browser, BrowserContext]:
    """Ensure VPN is up and a debug Edge pointed at EIP is running, then
    attach Playwright to it. Playwright only reads/fills the DOM here -
    it never navigates, since CDP-driven navigation doesn't get automatic
    NTLM SSO the way a command-line-argument launch does.
    """
    if not ensure_vpn_connected():
        raise VpnRequiredError(
            "連不到 EIP，且等待 VPN 連線逾時。請確認 FortiClient 是否已連線成功再重試。"
        )

    try:
        ensure_debug_edge(EIP_URL)
    except CdpConnectionError:
        # Auto-launch can get stuck in a slow NTLM/DNS retry loop on a
        # flaky network - fall back to the manual path rather than just
        # failing outright, so the tool still works even when the
        # automatic route doesn't settle in time.
        exe, *rest = edge_launch_args(EIP_URL)
        manual_cmd = " ".join([f'"{exe}"'] + [f'"{a}"' if " " in a else a for a in rest])
        raise CdpConnectionError(
            "自動開啟 Edge 逾時，可能是網路連線不穩定。請自己執行以下指令開啟 Edge 並確認登入成功，"
            "再重新執行本程式：\n"
            f"  {manual_cmd}"
        )

    try:
        browser = playwright.chromium.connect_over_cdp(CDP_URL)
    except Exception as e:  # noqa: BLE001 - surfaced as a clear setup error
        raise CdpConnectionError(f"無法連線到 {CDP_URL}：{e}") from e
    context = browser.contexts[0] if browser.contexts else browser.new_context()

    # Playwright can take a beat to finish enumerating the CDP session's
    # existing targets even though connect_over_cdp() has already
    # returned - context.pages can briefly appear empty right after
    # connecting even though the raw /json endpoint already lists the
    # tab. Give it a moment so callers relying on find_existing_page()
    # don't race ahead and wrongly conclude no tab exists yet.
    deadline = time.time() + 5
    while not context.pages and time.time() < deadline:
        time.sleep(0.2)

    return browser, context


def find_existing_page(context: BrowserContext, url_fragment: str):
    for page in context.pages:
        if url_fragment in page.url:
            return page
    return None
