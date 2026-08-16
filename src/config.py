"""Single source of configuration, loaded once from .env.

Importing this module loads .env, so any module that reads settings should
get them from here rather than touching os.environ directly - otherwise a
module imported before .env is read silently falls back to the placeholder
host and quietly targets nothing.

Only EIP_URL needs to be set: every other host and fragment in the project
is derived from it, so pointing the tool at a different instance is a
one-line change. The committed defaults are RFC 2606 documentation
placeholders, never a real system.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

load_dotenv(ROOT / ".env")

DEFAULT_EIP_URL = "http://eip.example.com/EFNET/"
DEFAULT_AUTH_ALLOWLIST = "*.example.com"


def host_of(url: str) -> str:
    """Bare hostname from a URL - no scheme, path or port."""
    return url.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]


EIP_URL = os.environ.get("EIP_URL", DEFAULT_EIP_URL)
EIP_HOST = host_of(EIP_URL)

# Domains Chromium may silently send Windows credentials to. Without this
# the dedicated debug profile prompts with a native credential dialog
# instead of completing SSO - see browser.py.
AUTH_SERVER_ALLOWLIST = os.environ.get("EIP_AUTH_ALLOWLIST", DEFAULT_AUTH_ALLOWLIST)

CDP_URL = os.environ.get("EIP_CDP_URL", "http://127.0.0.1:9222")

EDGE_EXE = os.environ.get(
    "EIP_EDGE_PATH", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)
EDGE_PROFILE_DIR = Path(
    os.environ.get("EIP_EDGE_PROFILE_DIR", str(ROOT / ".edge-profile"))
)
FORTICLIENT_PATH = os.environ.get(
    "FORTICLIENT_PATH", r"C:\Program Files\Fortinet\FortiClient\FortiClient.exe"
)


def is_placeholder_config() -> bool:
    """True when EIP_URL is still the shipped placeholder - i.e. .env has
    not been filled in. Callers can use this to fail with a useful message
    instead of a confusing DNS error."""
    return EIP_HOST == host_of(DEFAULT_EIP_URL)
