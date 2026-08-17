import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import browser  # noqa: E402


def test_launch_args_include_the_auth_allowlist():
    """Without this flag the dedicated debug profile shows a native Windows
    credential dialog instead of completing SSO, and the tab ends up on
    chrome-error://chromewebdata/ - which was misdiagnosed for a long time
    as flaky NTLM negotiation."""
    args = browser.edge_launch_args(browser.EIP_URL)
    assert any(a.startswith("--auth-server-allowlist=") for a in args)
    assert browser.AUTH_SERVER_ALLOWLIST in " ".join(args)


def test_profile_path_is_a_single_argv_element():
    """Regression guard: the profile path contains spaces ("OneDrive -
    example.com"). Passing it through anything that splits on whitespace
    truncated it, and Edge treated the tail as a URL - which once wrote a
    whole browser profile into an unintended directory."""
    args = browser.edge_launch_args(browser.EIP_URL)
    profile_args = [a for a in args if a.startswith("--user-data-dir=")]
    assert len(profile_args) == 1
    assert str(browser.EDGE_PROFILE_DIR) == profile_args[0].split("=", 1)[1]


def test_url_is_passed_as_a_launch_argument_not_navigated_to():
    """SSO only completes for a URL given at launch; a CDP-driven
    navigation to the same URL is blocked."""
    args = browser.edge_launch_args(browser.EIP_URL)
    assert args[-1] == browser.EIP_URL
    assert args[0] == browser.EDGE_EXE


def test_debug_port_flag_present_and_single():
    args = browser.edge_launch_args(browser.EIP_URL)
    assert args.count("--remote-debugging-port=9222") == 1


def test_launch_args_are_all_strings():
    """subprocess.Popen on Windows rejects a PosixPath silently-ish; keep
    everything stringified at the boundary."""
    args = browser.edge_launch_args(browser.EIP_URL)
    assert all(isinstance(a, str) for a in args)


def test_ensure_debug_edge_reports_a_missing_edge_binary(monkeypatch):
    """Regression: moving configuration into config.py once dropped
    `from pathlib import Path` while these existence checks still used it,
    so this function raised NameError at runtime. The unit tests passed
    because nothing exercised it - hence this one."""
    monkeypatch.setattr(browser, "EDGE_EXE", r"C:\definitely\not\here\msedge.exe")

    with pytest.raises(browser.CdpConnectionError):
        browser.ensure_debug_edge("http://eip.example.com/EFNET/")


def test_launch_forticlient_reports_a_missing_binary(monkeypatch):
    """Same Path-usage path as above, different function."""
    monkeypatch.setattr(browser, "FORTICLIENT_PATH", r"C:\definitely\not\here\FortiClient.exe")
    assert browser.launch_forticlient() is False


class FakeChromium:
    def __init__(self, fail_times=0):
        self.calls = 0
        self.fail_times = fail_times
        self.timeouts = []

    def connect_over_cdp(self, url, timeout=None):
        self.calls += 1
        self.timeouts.append(timeout)
        if self.calls <= self.fail_times:
            raise TimeoutError("Timeout exceeded")
        return f"browser-{self.calls}"


class FakePlaywright:
    def __init__(self, chromium):
        self.chromium = chromium


@pytest.fixture
def no_restart_side_effects(monkeypatch):
    """Neutralize the parts of a restart that touch the real machine."""
    killed = []
    relaunched = []
    monkeypatch.setattr(browser, "_kill_debug_edge", lambda: killed.append(True))
    monkeypatch.setattr(browser, "_ensure_debug_edge_or_explain", lambda: relaunched.append(True))
    monkeypatch.setattr(browser.time, "sleep", lambda s: None)
    return killed, relaunched


def test_connect_does_not_restart_when_the_first_attempt_works(no_restart_side_effects):
    killed, relaunched = no_restart_side_effects
    chromium = FakeChromium(fail_times=0)

    result = browser._connect_with_recovery(FakePlaywright(chromium))

    assert result == "browser-1"
    assert killed == [] and relaunched == []


def test_connect_restarts_the_browser_once_when_it_hangs(no_restart_side_effects):
    """The observed failure: the CDP websocket connects but target
    enumeration never completes. Restarting always cured it."""
    killed, relaunched = no_restart_side_effects
    chromium = FakeChromium(fail_times=1)

    result = browser._connect_with_recovery(FakePlaywright(chromium))

    assert result == "browser-2"
    assert killed == [True], "應該先關掉卡住的瀏覽器"
    assert relaunched == [True], "然後重新啟動一個"


def test_connect_gives_up_after_one_restart(no_restart_side_effects):
    """A freshly launched browser that still will not talk is not a
    problem restarting again would solve."""
    chromium = FakeChromium(fail_times=99)

    with pytest.raises(browser.CdpConnectionError) as excinfo:
        browser._connect_with_recovery(FakePlaywright(chromium))

    assert chromium.calls == 2, "只重試一次，不無限重啟"
    assert "msedge.exe" in str(excinfo.value), "失敗訊息要附上手動啟動指令"


def test_connect_uses_a_short_timeout_not_playwrights_180s_default(no_restart_side_effects):
    """A hang needs to be detected quickly - the fix is a restart, and
    waiting three minutes first just delays it."""
    chromium = FakeChromium(fail_times=0)

    browser._connect_with_recovery(FakePlaywright(chromium))

    assert chromium.timeouts == [browser.CONNECT_TIMEOUT_MS]
    assert browser.CONNECT_TIMEOUT_MS < 180_000
