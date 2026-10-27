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
automatically and pops a native Windows credential dialog
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
import os
import socket
import shutil
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


def _debug_edge_pids_by_profile() -> list:
    """PIDs of msedge processes launched against our own debug profile,
    found by command line rather than by port.

    Needed because a launch can leave Edge alive with the DevTools server
    never started - no DevToolsActivePort, nothing listening on 9222 - and
    a port-based lookup then finds nothing to kill. Meanwhile the dead
    instance still owns the profile, so every subsequent launch just hands
    its URL to it and exits, and the retry loop spins without effect.

    Matching is on the profile directory, which only our own launches ever
    pass, so the user's real browser windows can never be selected.
    """
    script = (
        "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | "
        "Where-Object { $_.CommandLine -like '*' + $env:EIP_DEBUG_PROFILE + '*' } | "
        "ForEach-Object { $_.ProcessId }"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "EIP_DEBUG_PROFILE": str(EDGE_PROFILE_DIR)},
        ).stdout
    except Exception:  # noqa: BLE001
        return []
    return [int(line) for line in out.split() if line.strip().isdigit()]


def _kill_debug_edge() -> None:
    """Kill our own dedicated debug-profile Edge instance - never the
    user's real browser windows.

    Two ways of identifying it, because neither alone is sufficient: the
    owner of port 9222 (which finds it even if the profile path is ever
    reconfigured) and any process whose command line carries our profile
    directory (which finds it when the DevTools server never came up, and
    catches the child processes that keep the profile locked).
    """
    pids = set(_debug_edge_pids_by_profile())
    port_pid = _pid_listening_on_port(9222)
    if port_pid is not None:
        pids.add(port_pid)
    for pid in pids:
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
        # A live instance that never opened the port would silently swallow
        # this launch: Edge hands the URL to the existing process for that
        # profile and exits immediately.
        if _debug_edge_pids_by_profile():
            _kill_debug_edge()
            time.sleep(2)
        EDGE_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
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
        raise CdpConnectionError(
            f"Edge not found at {EDGE_EXE}. Set the EIP_EDGE_PATH environment variable."
        )

    for attempt in range(1, attempts + 1):
        if _launch_debug_edge_once(url, settle_timeout_seconds):
            return
        if attempt < attempts:
            _kill_debug_edge()
            time.sleep(1)

    # Last resort: the profile itself wedges. Edge then starts, spawns its
    # child processes and never brings up the DevTools server - no
    # DevToolsActivePort, nothing on the debug port - and no number of
    # relaunches recovers it. Observed twice in one afternoon. Recreating
    # the profile fixes it every time, and costs nothing: it holds no user
    # data, and --auth-server-allowlist signs a fresh one back in silently.
    _kill_debug_edge()
    time.sleep(1)
    if _discard_wedged_profile():
        print("[warn] Edge would not open its debug port; discarded the profile "
              "and launching a fresh one.")
        if _launch_debug_edge_once(url, settle_timeout_seconds):
            return

    raise CdpConnectionError(
        f"Timed out launching Edge after {attempts} attempts (and once more with a "
        "fresh profile) - it may be stuck retrying NTLM/DNS. Check the network "
        "connection."
    )


# Files Chromium always leaves in a profile it has actually used. Requiring
# one of them keeps the reset below from ever deleting something that is not
# a browser profile, however EIP_EDGE_PROFILE_DIR is set.
PROFILE_MARKERS = ("Local State", "Default")


def _discard_wedged_profile() -> bool:
    """Delete the debug profile so the next launch builds a fresh one.

    Returns False without touching anything unless the configured directory
    really looks like a Chromium profile - this deletes a whole tree, and
    the path comes from an environment variable.
    """
    profile = EDGE_PROFILE_DIR
    if not profile.is_dir():
        return False
    if not any((profile / marker).exists() for marker in PROFILE_MARKERS):
        print(f"[warn] {profile} does not look like a browser profile; leaving it alone.")
        return False
    try:
        shutil.rmtree(profile)
        return True
    except Exception as e:  # noqa: BLE001 - a failed reset is not fatal on its own
        print(f"[warn] could not remove the wedged profile ({type(e).__name__}: {e}).")
        return False


# Playwright's own default is 180s. That is far too patient for a wedged
# browser: the failure mode is a hang, not slowness, and every second spent
# waiting is a second not spent on the restart that actually fixes it.
CONNECT_TIMEOUT_MS = int(os.environ.get("EIP_CDP_CONNECT_TIMEOUT_MS", "30000"))


def _connect_with_recovery(playwright: Playwright) -> Browser:
    """connect_over_cdp, restarting the browser once if it hangs.

    Only the first attempt is forgiving. If a freshly launched browser also
    refuses to hand over a CDP session, something is wrong that restarting
    will not fix, and looping would just delay a human finding out.
    """
    try:
        return playwright.chromium.connect_over_cdp(CDP_URL, timeout=CONNECT_TIMEOUT_MS)
    except Exception as first_error:  # noqa: BLE001 - any failure means "try a restart"
        print(f"[warn] CDP connection failed ({type(first_error).__name__}); "
              "treating the debug Edge as wedged, restarting and trying once more...")

    _kill_debug_edge()
    time.sleep(2)
    _ensure_debug_edge_or_explain()

    try:
        browser = playwright.chromium.connect_over_cdp(CDP_URL, timeout=CONNECT_TIMEOUT_MS)
    except Exception as e:  # noqa: BLE001
        raise CdpConnectionError(
            f"Still cannot connect to {CDP_URL} after restarting Edge: {e}\n"
            "Launch Edge yourself with the command below, confirm you are logged in, "
            "then run this program again:\n"
            f"  {_manual_launch_command()}"
        ) from e
    print("[info] Connected after restart.")
    return browser


def _manual_launch_command() -> str:
    exe, *rest = edge_launch_args(EIP_URL)
    return " ".join([f'"{exe}"'] + [f'"{a}"' if " " in a else a for a in rest])


def _ensure_debug_edge_or_explain() -> None:
    try:
        ensure_debug_edge(EIP_URL)
    except CdpConnectionError:
        # Auto-launch can get stuck in a slow NTLM/DNS retry loop on a
        # flaky network - fall back to the manual path rather than just
        # failing outright, so the tool still works even when the
        # automatic route doesn't settle in time.
        raise CdpConnectionError(
            "Timed out launching Edge automatically - the network may be unstable. "
            "Launch it yourself with the command below, confirm you are logged in, "
            "then run this program again:\n"
            f"  {_manual_launch_command()}"
        )


def attach_context(playwright: Playwright, fresh_session: bool = False) -> tuple[Browser, BrowserContext]:
    """Ensure VPN is up and a debug Edge pointed at EIP is running, then
    attach Playwright to it. Playwright only reads/fills the DOM here -
    it never navigates, since CDP-driven navigation doesn't get automatic
    NTLM SSO the way a command-line-argument launch does.

    fresh_session closes any running debug Edge first so the browser logs
    in anew. Needed after an HTTP lookup (duplicate_check.find_rows_via_http):
    each user gets a single EIP session, the HTTP login took it over, and an
    Edge that was already open is left holding a dead one.

    A long-running debug Edge can reach a state where the CDP websocket
    still accepts a connection but connect_over_cdp then hangs during
    target enumeration - observed repeatedly, and always cured by
    restarting the browser (it began after Edge auto-updated underneath a
    running instance). So a hang here is treated as a wedged browser: kill
    it, relaunch, and try once more, instead of making a human notice and
    do exactly that by hand.
    """
    if not ensure_vpn_connected():
        raise VpnRequiredError(
            "EIP is unreachable and waiting for the VPN timed out. "
            "Check that FortiClient has connected, then retry."
        )

    if fresh_session:
        _kill_debug_edge()
    _ensure_debug_edge_or_explain()

    try:
        browser = _connect_with_recovery(playwright)
    except CdpConnectionError:
        raise
    except Exception as e:  # noqa: BLE001 - surfaced as a clear setup error
        raise CdpConnectionError(f"Cannot connect to {CDP_URL}: {e}") from e
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
