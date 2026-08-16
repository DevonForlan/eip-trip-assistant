"""Offline dry run: fetch ESSF21, parse it, build the POST payload, print
a sanitized diff. Nothing is sent.

Verifies the two things that must hold before any postback work begins:
  - the parser preserves every control the server sent (especially all 63
    hidden fields - dropping one silently corrupts a postback)
  - trip data lands on the right POST names, resolved from the HTML rather
    than by transforming ids

Output is sanitized by construction: field names, lengths, and flags only.
__VIEWSTATE / __MSPVSTATE / __MSPVSTATE_ZIP values, the Identifier, cookie
values and the trip's own text are never printed - the sample trip data
below is obvious dummy text anyway, so no real trip information is
involved in a dry run.

Run:
    python scripts/http_trip_payload_dry_run.py
"""
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlparse

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import http_trip_form  # noqa: E402
import webforms_state  # noqa: E402
from http_eip_client import HttpEipClient, HttpEipError  # noqa: E402

SENSITIVE_QUERY_PARAMS = {"identifier", "loginid", "clientip"}


@dataclass
class SampleTrip:
    """Obvious dummy data - a dry run must not involve a real trip."""
    date: str = "2026/01/01"
    start_time: str = "09:00"
    end_time: str = "18:30"
    location: str = "測試地點測試地點"
    reason: str = "測試事由"
    transport: str = "測試交通"
    note: str = "測試備註"


def mask_url(url: str) -> str:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    if not pairs:
        return base
    parts = [
        f"{k}=<已遮罩,len={len(v)}>" if k.lower() in SENSITIVE_QUERY_PARAMS else f"{k}={v}"
        for k, v in pairs
    ]
    return f"{base}?{'&'.join(parts)}"


def raw_counts(html: str) -> dict:
    """Independent regex count over the raw HTML, used to catch a parser
    that silently drops controls."""
    scripts = "".join(re.findall(r"<script\b.*?</script>", html, re.I | re.S))
    counts = {
        "input": len(re.findall(r"<input[\s>]", html, re.I)),
        "textarea": len(re.findall(r"<textarea[\s>]", html, re.I)),
        "select": len(re.findall(r"<select[\s>]", html, re.I)),
        "input_in_script": len(re.findall(r"<input[\s>]", scripts, re.I)),
    }
    by_type = {}
    for m in re.finditer(r"<input([^>]*)>", html, re.I):
        t = re.search(r'type\s*=\s*"?(\w+)"?', m.group(1), re.I)
        key = t.group(1).lower() if t else "text"
        by_type[key] = by_type.get(key, 0) + 1
    counts["by_type"] = by_type
    return counts


def main():
    print("=== ESSF21 Payload Dry Run（只 GET，不 POST）===\n")

    client = HttpEipClient()  # read_only=True by default: POST is blocked in code
    try:
        print("步驟 1-4：authenticate -> initialize_efnet -> open_trip_wrapper -> open_trip_form")
        page = client.prepare()
    except HttpEipError as e:
        print(f"\n[error] {e}")
        return 1

    print(f"  ASP.NET_SessionId 是否取得：{'是' if client.has_session_cookie else '否'}")
    print(f"  EPIE001 大小：{len(client.wrapper_html.encode('utf-8', errors='replace')):,} bytes")
    print(f"  ESSF21 網址：{mask_url(page.url)}")
    print(f"  ESSF21 大小：{page.byte_length:,} bytes")

    # --- parse ------------------------------------------------------
    print("\n=== Parser 結果 ===")
    form = webforms_state.parse_form(page.html)
    counts = form.counts()
    print(f"  form: name={form.name!r} method={form.method!r}")
    print(f"  form action（已遮罩）：{mask_url(urljoin(page.url, form.action))}")
    for k in ("total_controls", "hidden", "text", "textarea", "checkbox", "radio",
              "submit", "image", "select", "other", "disabled", "unnamed",
              "successful_controls"):
        print(f"    {k:22s} {counts[k]}")

    # --- consistency check (item 七) --------------------------------
    print("\n=== 一致性檢查（parser vs 原始 HTML regex）===")
    raw = raw_counts(page.html)
    parsed_inputs = counts["total_controls"] - counts["textarea"] - counts["select"]
    checks = [
        ("input 總數", parsed_inputs, raw["input"]),
        ("textarea 總數", counts["textarea"], raw["textarea"]),
        ("select 總數", counts["select"], raw["select"]),
        ("hidden 欄位", counts["hidden"], raw["by_type"].get("hidden", 0)),
        ("text 欄位", counts["text"], raw["by_type"].get("text", 0)),
        ("checkbox", counts["checkbox"], raw["by_type"].get("checkbox", 0)),
        ("radio", counts["radio"], raw["by_type"].get("radio", 0)),
        ("submit", counts["submit"], raw["by_type"].get("submit", 0)),
        ("image", counts["image"], raw["by_type"].get("image", 0)),
    ]
    all_ok = True
    for label, parsed_n, raw_n in checks:
        ok = parsed_n == raw_n
        all_ok = all_ok and ok
        print(f"  {'OK  ' if ok else 'FAIL'} {label:14s} parser={parsed_n:<5d} 原始HTML={raw_n}")
    print(f"  （原始 HTML 的 <script> 內含 input 數：{raw['input_in_script']}，"
          "parser 會略過 script 內容）")

    if not all_ok:
        print("\n[stop] parser 與原始 HTML 不一致 - 依指示先修 parser，不進行任何 POST 相關工作。")
        return 1
    print("  -> 全部一致，沒有漏掉任何控制項。")

    # --- ASP.NET state ---------------------------------------------
    print("\n=== ASP.NET state 欄位（只顯示存在與長度，不顯示內容）===")
    for s in form.state_field_summary():
        if s["present"]:
            print(f"  {s['name']:24s} preserved=True   length={s['length']:,}")
        else:
            print(f"  {s['name']:24s} 不存在（這個頁面沒有這個欄位）")

    # --- checkbox / radio -------------------------------------------
    print("\n=== checkbox / radio 狀態（決定是否會被送出）===")
    for c in form.controls:
        if c.effective_type in ("checkbox", "radio"):
            print(f"  {c.effective_type:8s} name={c.name:26s} "
                  f"checked={str(c.checked):5s} -> {'會送出' if c.checked else '不會送出'}")

    # --- build payload ----------------------------------------------
    print("\n=== 建立 payload（僅記憶體，不送出）===")
    trip = SampleTrip()
    try:
        payload = http_trip_form.build_trip_payload(
            form, trip, action_url=urljoin(page.url, form.action)
        )
    except http_trip_form.PayloadBuildError as e:
        print(f"\n[error] {e}")
        return 1

    print(f"  method={payload.method}  欄位總數={len(payload.fields)}  "
          f"不重複 name={len(set(payload.field_names()))}")
    print(f"  action（已遮罩）：{mask_url(payload.action_url)}")

    print("\n--- 修改的欄位 diff（只顯示長度）---")
    for ch in payload.changes:
        print(f"  {ch.post_name}:")
        print(f"      logical={ch.logical}  tag=<{ch.tag}>  hidden={ch.is_hidden}")
        print(f"      old_present={ch.old_present}  old_length={ch.old_length}  "
              f"new_length={ch.new_length}")

    print("\n--- 保留的 state 欄位 ---")
    for name in webforms_state.OPAQUE_STATE_FIELDS:
        ln = payload.value_length(name)
        if ln is None:
            print(f"  {name:24s} 不在送出清單")
        else:
            print(f"  {name:24s} preserved=True  length={ln:,}")

    print("\n--- payload 中未被修改的欄位（只列名稱數量）---")
    changed = {ch.post_name for ch in payload.changes}
    untouched = [n for n in payload.field_names() if n not in changed]
    print(f"  共 {len(untouched)} 個原樣保留（其中 hidden {counts['hidden']} 個全部保留）")

    print("\n=== 完成：沒有送出任何請求（本腳本只做 GET）===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
