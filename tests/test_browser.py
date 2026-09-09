import subprocess
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
    assert killed == [True], "should kill the wedged browser first"
    assert relaunched == [True], "then launch a fresh one"


def test_connect_gives_up_after_one_restart(no_restart_side_effects):
    """A freshly launched browser that still will not talk is not a
    problem restarting again would solve."""
    chromium = FakeChromium(fail_times=99)

    with pytest.raises(browser.CdpConnectionError) as excinfo:
        browser._connect_with_recovery(FakePlaywright(chromium))

    assert chromium.calls == 2, "retries exactly once - never restarts in a loop"
    assert "msedge.exe" in str(excinfo.value), "failure text must include the manual launch command"


def test_connect_uses_a_short_timeout_not_playwrights_180s_default(no_restart_side_effects):
    """A hang needs to be detected quickly - the fix is a restart, and
    waiting three minutes first just delays it."""
    chromium = FakeChromium(fail_times=0)

    browser._connect_with_recovery(FakePlaywright(chromium))

    assert chromium.timeouts == [browser.CONNECT_TIMEOUT_MS]
    assert browser.CONNECT_TIMEOUT_MS < 180_000


def test_kill_debug_edge_finds_the_instance_when_the_port_never_opened(monkeypatch):
    """The failure this guards against: Edge alive, DevTools server never
    started, so nothing is listening on 9222. A port-only lookup kills
    nothing, the dead instance keeps the profile, and every relaunch is
    silently swallowed by it."""
    killed = []
    monkeypatch.setattr(browser, "_pid_listening_on_port", lambda port: None)
    monkeypatch.setattr(browser, "_debug_edge_pids_by_profile", lambda: [30560, 7396])
    monkeypatch.setattr(
        browser.subprocess, "run",
        lambda args, **kw: killed.append(args) or subprocess.CompletedProcess(args, 0),
    )

    browser._kill_debug_edge()

    assert sorted(a[2] for a in killed) == ["30560", "7396"]
    assert all(a[0] == "taskkill" and a[-1] == "/F" for a in killed)


def test_kill_debug_edge_combines_both_lookups_without_duplicates(monkeypatch):
    killed = []
    monkeypatch.setattr(browser, "_pid_listening_on_port", lambda port: 30560)
    monkeypatch.setattr(browser, "_debug_edge_pids_by_profile", lambda: [30560, 7396])
    monkeypatch.setattr(
        browser.subprocess, "run",
        lambda args, **kw: killed.append(args) or subprocess.CompletedProcess(args, 0),
    )

    browser._kill_debug_edge()

    assert sorted(a[2] for a in killed) == ["30560", "7396"]


def test_launch_clears_a_stale_instance_before_relaunching(monkeypatch):
    """Launching on top of an instance that still owns the profile is a
    no-op - Edge hands over the URL and exits - so the stale one has to go
    first."""
    calls = []
    monkeypatch.setattr(browser, "_cdp_port_is_up", lambda: False)
    monkeypatch.setattr(browser, "_debug_edge_pids_by_profile", lambda: [30560])
    monkeypatch.setattr(browser, "_kill_debug_edge", lambda: calls.append("kill"))
    monkeypatch.setattr(browser.time, "sleep", lambda s: None)
    monkeypatch.setattr(browser.subprocess, "Popen", lambda args: calls.append("launch"))
    monkeypatch.setattr(browser.time, "time", lambda: 1e9)  # deadline already passed

    browser._launch_debug_edge_once("http://eip.example.com/EFNET/", 0)

    assert calls == ["kill", "launch"], calls


def test_profile_is_discarded_when_no_launch_ever_opens_the_port(monkeypatch, tmp_path):
    """The profile itself can wedge: Edge starts, spawns its children and
    never brings up the DevTools server, and no number of relaunches
    recovers it. Recreating the profile does."""
    profile = tmp_path / "edge-profile"
    (profile / "Default").mkdir(parents=True)
    (profile / "Local State").write_text("{}", encoding="utf-8")

    fake_exe = tmp_path / "msedge.exe"
    fake_exe.write_text("", encoding="utf-8")

    attempts = []
    monkeypatch.setattr(browser, "EDGE_PROFILE_DIR", profile)
    monkeypatch.setattr(browser, "EDGE_EXE", str(fake_exe))
    monkeypatch.setattr(browser, "_kill_debug_edge", lambda: None)
    monkeypatch.setattr(browser.time, "sleep", lambda s: None)

    def fake_launch(url, settle):
        attempts.append(profile.exists())
        return not profile.exists()  # only a fresh profile succeeds

    monkeypatch.setattr(browser, "_launch_debug_edge_once", fake_launch)

    browser.ensure_debug_edge("http://eip.example.com/EFNET/", attempts=2)

    assert attempts == [True, True, False], attempts
    assert not profile.exists(), "the wedged profile should have been discarded"


def test_a_directory_that_is_not_a_profile_is_never_deleted(monkeypatch, tmp_path):
    """EIP_EDGE_PROFILE_DIR comes from the environment and this deletes a
    whole tree, so it must refuse anything without Chromium's own markers."""
    not_a_profile = tmp_path / "important"
    not_a_profile.mkdir()
    (not_a_profile / "notes.txt").write_text("keep me", encoding="utf-8")

    monkeypatch.setattr(browser, "EDGE_PROFILE_DIR", not_a_profile)

    assert browser._discard_wedged_profile() is False
    assert (not_a_profile / "notes.txt").exists()


def test_discarding_an_absent_profile_is_a_no_op(monkeypatch, tmp_path):
    monkeypatch.setattr(browser, "EDGE_PROFILE_DIR", tmp_path / "nope")
    assert browser._discard_wedged_profile() is False
