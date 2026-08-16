"""Network request/response logging for specific actions (儲存/傳送).

Records enough to reconstruct what an ASP.NET postback actually did,
instead of guessing from screenshots - the recurring problem during the
2026-08 testing session ("儲存" once silently redirected to a
session-expired page instead of saving, and it took several rounds of
manual poking to figure that out).

Safety rule (also an org data-handling requirement): Authorization and
Cookie/Set-Cookie headers are always masked. POST body field VALUES are
never recorded, even for fields that look harmless - only field NAMES
(e.g. "ESSCCDJ028$txt"), since a postback body can contain arbitrary
values (including VIEWSTATE, session-related hidden fields) that this
module has no reliable way to pre-classify as safe to persist.
"""
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qsl

SENSITIVE_HEADER_NAMES = {"authorization", "cookie", "set-cookie"}


def mask_headers(headers: dict) -> dict:
    return {
        k: ("***MASKED***" if k.lower() in SENSITIVE_HEADER_NAMES else v)
        for k, v in headers.items()
    }


def post_field_names(post_data) -> list:
    """Field NAMES only from a form-encoded POST body - never values."""
    if not post_data:
        return []
    try:
        pairs = parse_qsl(post_data, keep_blank_values=True)
    except Exception:  # noqa: BLE001
        return ["<unparseable POST body>"]
    return [name for name, _ in pairs]


@dataclass
class NetworkEvent:
    kind: str  # "request" | "response" | "requestfailed"
    method: str = ""
    url: str = ""
    status: int | None = None
    post_fields: list = field(default_factory=list)
    failure: str = ""
    timestamp: float = 0.0


class NetworkRecorder:
    """Attach around a single action (e.g. one button click) to record
    what it actually did at the network level."""

    def __init__(self, label: str):
        self.label = label
        self.events: list[NetworkEvent] = []
        self._page = None

    def _on_request(self, request) -> None:
        self.events.append(
            NetworkEvent(
                kind="request",
                method=request.method,
                url=request.url,
                post_fields=post_field_names(getattr(request, "post_data", None)),
                timestamp=time.time(),
            )
        )

    def _on_response(self, response) -> None:
        self.events.append(
            NetworkEvent(
                kind="response",
                method=response.request.method,
                url=response.url,
                status=response.status,
                timestamp=time.time(),
            )
        )

    def _on_request_failed(self, request) -> None:
        self.events.append(
            NetworkEvent(
                kind="requestfailed",
                method=request.method,
                url=request.url,
                failure=str(getattr(request, "failure", "") or ""),
                timestamp=time.time(),
            )
        )

    def attach(self, page) -> "NetworkRecorder":
        self._page = page
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        page.on("requestfailed", self._on_request_failed)
        return self

    def detach(self) -> None:
        if self._page is None:
            return
        self._page.remove_listener("request", self._on_request)
        self._page.remove_listener("response", self._on_response)
        self._page.remove_listener("requestfailed", self._on_request_failed)
        self._page = None

    def redirect_chain(self) -> list:
        return [f"{e.status} {e.url}" for e in self.events if e.kind == "response"]

    def had_failure(self) -> bool:
        return any(e.kind == "requestfailed" for e in self.events)

    def to_log_lines(self) -> list:
        lines = [f"=== network log: {self.label} ==="]
        for e in self.events:
            if e.kind == "request":
                lines.append(f"[request] {e.method} {e.url} fields={e.post_fields}")
            elif e.kind == "response":
                lines.append(f"[response] {e.status} {e.url}")
            else:
                lines.append(f"[requestfailed] {e.method} {e.url} ({e.failure})")
        return lines

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self.to_log_lines()), encoding="utf-8")
