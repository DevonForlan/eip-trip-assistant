import sys
from pathlib import Path

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
