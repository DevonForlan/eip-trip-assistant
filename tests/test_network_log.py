import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from network_log import NetworkRecorder, mask_headers, post_field_names  # noqa: E402


class FakeRequest:
    def __init__(self, method, url, post_data=None, failure=None):
        self.method = method
        self.url = url
        self.post_data = post_data
        self.failure = failure


class FakeResponse:
    def __init__(self, request, status):
        self.request = request
        self.url = request.url
        self.status = status


class FakePage:
    def __init__(self):
        self.listeners = {}

    def on(self, event, handler):
        self.listeners[event] = handler

    def remove_listener(self, event, handler):
        self.listeners.pop(event, None)


def test_mask_headers_hides_authorization_and_cookie():
    headers = {"Authorization": "Bearer xyz", "Cookie": "sid=abc", "Content-Type": "text/html"}
    masked = mask_headers(headers)
    assert masked["Authorization"] == "***MASKED***"
    assert masked["Cookie"] == "***MASKED***"
    assert masked["Content-Type"] == "text/html"


def test_post_field_names_never_includes_values():
    names = post_field_names("__VIEWSTATE=SecretBlob123&ESSCCDJ028%24txt=%E5%85%A8%E7%A4%BE")
    assert "__VIEWSTATE" in names
    assert "ESSCCDJ028$txt" in names
    assert "SecretBlob123" not in str(names)
    assert "全社" not in str(names)


def test_recorder_captures_request_response_and_masks_field_values():
    page = FakePage()
    recorder = NetworkRecorder("儲存")
    recorder.attach(page)

    req = FakeRequest("POST", "http://eip.example.com/EFNET/save", post_data="__VIEWSTATE=abc123&foo=bar")
    page.listeners["request"](req)
    page.listeners["response"](FakeResponse(req, 200))

    recorder.detach()

    lines = recorder.to_log_lines()
    joined = "\n".join(lines)
    assert "__VIEWSTATE" in joined
    assert "abc123" not in joined  # value never logged
    assert "[response] 200" in joined
    assert "dialog" not in page.listeners and "request" not in page.listeners  # cleaned up


def test_recorder_flags_request_failures():
    page = FakePage()
    recorder = NetworkRecorder("傳送")
    recorder.attach(page)

    req = FakeRequest("POST", "http://eip.example.com/EFNET/send", failure="net::ERR_ABORTED")
    page.listeners["requestfailed"](req)
    recorder.detach()

    assert recorder.had_failure()
    assert "requestfailed" in recorder.to_log_lines()[1]


def test_recorder_save_writes_file(tmp_path):
    page = FakePage()
    recorder = NetworkRecorder("test")
    recorder.attach(page)
    recorder.detach()

    out = tmp_path / "sub" / "log.txt"
    recorder.save(out)

    assert out.exists()
    assert "network log: test" in out.read_text(encoding="utf-8")
