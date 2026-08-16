"""
Phase 1 - Website exploration / DOM analysis for the EIP portal.

EIP requires Windows Integrated Authentication (NTLM/Negotiate) that
Playwright cannot complete when it launches its own fresh browser - there
is no automatic SSO and no native credential prompt is surfaced, it just
fails the navigation outright. So instead of launching a new browser, this
script ATTACHES to a real Edge window you start yourself (see the
--remote-debugging-port command printed below) and that you log into
normally. Automation then reuses that already-authenticated session.

What this script does:
  1. Connects to an Edge instance you already launched + logged into
     (via the Chrome DevTools Protocol). No password is ever read,
     stored, or typed by this script.
  2. Analyzes the homepage DOM (including all frames) and locates the
     "出差登記" element by inspecting real DOM text/attributes - it does
     NOT assume a fixed selector.
  3. Clicks it, detects whether that opens a popup window, navigates the
     same page, or loads content into a frame.
  4. Analyzes the resulting form's DOM: every input / select / textarea /
     button / iframe, across all frames, with a best-effort label guess
     and both a CSS path and an XPath.
  5. Writes everything to docs/eip-analysis.md and screenshots/*.png.
  6. Writes a machine-readable draft to config/selectors.discovered.json
     for Phase 2 to consume (this file is gitignored - it can reveal
     internal system structure).

This script NEVER fills in or submits any form. It only reads the DOM.
It also NEVER closes the Edge window it attaches to - that is your real
browser, closing it would kill your other tabs/session too.

Usage:
    1) Run the printed msedge.exe command once, log into EIP in that window.
    2) python scripts/inspect_eip.py

Recommended: run this directly in your own terminal (not through an
automated tool) since step 1 requires you to interact with the browser
window yourself.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import browser as browser_mod  # noqa: E402

load_dotenv(ROOT / ".env")

EIP_URL = os.environ.get("EIP_URL", "http://eip.example.com/EFNET/")
EIP_URL_FRAGMENT = EIP_URL.split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]
SCREENSHOT_DIR = ROOT / "screenshots"
DOCS_PATH = ROOT / "docs" / "eip-analysis.md"
DISCOVERED_JSON_PATH = ROOT / "config" / "selectors.discovered.json"
EDGE_EXE = os.environ.get(
    "EIP_EDGE_PATH", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
)
EDGE_PROFILE_DIR = ROOT / ".edge-profile"

# Candidate texts to look for, in priority order. The actual label on a
# 15+ year old ASP.NET portal might not be exactly "出差登記" - all
# candidates that match are recorded so a human can confirm the right one.
TRIGGER_TEXT_CANDIDATES = ["出差登記", "出差申請", "出差"]

INTERACTIVE_TAGS = ["input", "select", "textarea", "button"]

SCREENSHOT_DIR.mkdir(exist_ok=True)
DISCOVERED_JSON_PATH.parent.mkdir(exist_ok=True)

# JS run inside the page to describe a single DOM element in detail.
# Kept as one shared function so homepage-trigger analysis and
# form-field analysis produce identically-shaped records.
EXTRACT_JS = """
el => {
    function cssPath(node) {
        if (!(node instanceof Element)) return '';
        const path = [];
        while (node && node.nodeType === Node.ELEMENT_NODE) {
            let selector = node.nodeName.toLowerCase();
            if (node.id) {
                path.unshift(selector + '#' + node.id);
                break;
            } else {
                let sib = node, nth = 1;
                while (sib.previousElementSibling) {
                    sib = sib.previousElementSibling;
                    if (sib.nodeName.toLowerCase() === selector) nth++;
                }
                if (nth !== 1) selector += ':nth-of-type(' + nth + ')';
            }
            path.unshift(selector);
            node = node.parentElement;
        }
        return path.join(' > ');
    }
    function xpath(node) {
        if (node.id) return '//*[@id="' + node.id + '"]';
        const parts = [];
        while (node && node.nodeType === Node.ELEMENT_NODE) {
            let idx = 1;
            let sib = node.previousElementSibling;
            while (sib) {
                if (sib.nodeName === node.nodeName) idx++;
                sib = sib.previousElementSibling;
            }
            parts.unshift(node.nodeName.toLowerCase() + '[' + idx + ']');
            node = node.parentElement;
        }
        return '/' + parts.join('/');
    }
    function findLabel(node) {
        if (node.id) {
            const lbl = document.querySelector('label[for="' + node.id + '"]');
            if (lbl) return lbl.innerText.trim();
        }
        const parentLabel = node.closest('label');
        if (parentLabel) return parentLabel.innerText.trim();
        const td = node.closest('td');
        if (td && td.previousElementSibling) {
            return td.previousElementSibling.innerText.trim();
        }
        const tr = node.closest('tr');
        if (tr) {
            const firstCell = tr.querySelector('td,th');
            if (firstCell && firstCell !== td) return firstCell.innerText.trim();
        }
        return null;
    }
    const tag = el.tagName.toLowerCase();
    const info = {
        tag: tag,
        id: el.id || null,
        name: el.getAttribute('name'),
        type: el.getAttribute('type'),
        className: el.className || null,
        placeholder: el.getAttribute('placeholder'),
        value: el.value !== undefined ? el.value : null,
        checked: el.checked !== undefined ? el.checked : null,
        disabled: !!el.disabled,
        readonly: !!el.readOnly,
        text: (el.innerText || '').trim().slice(0, 80),
        onclick: el.getAttribute('onclick'),
        href: el.getAttribute('href'),
        outerHTML: el.outerHTML.slice(0, 300),
        cssPath: cssPath(el),
        xpath: xpath(el),
        visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
        label: findLabel(el),
    };
    if (tag === 'select') {
        info.options = Array.from(el.options).map(o => (
            {value: o.value, text: o.text.trim(), selected: o.selected}
        ));
    }
    return info;
}
"""


def now_str() -> str:
    tz = timezone(timedelta(hours=8))  # Asia/Taipei
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %z")


def shot(page, name: str) -> str:
    path = SCREENSHOT_DIR / name
    try:
        page.screenshot(path=str(path), full_page=True)
        print(f"  [screenshot] {path}")
    except PlaywrightError as e:
        print(f"  [screenshot failed] {name}: {e}")
    return name


def list_frames(page) -> list[dict]:
    frames = []
    for f in page.frames:
        frames.append({
            "name": f.name,
            "url": f.url,
            "is_main": f == page.main_frame,
        })
    return frames


def find_trigger_candidates(page) -> dict:
    """Search every frame for elements whose direct text matches a
    candidate trigger label. Returns all matches - does not pick a
    winner - so a human can confirm which one is correct.
    """
    result = {"matched_text": None, "candidates": []}
    for text in TRIGGER_TEXT_CANDIDATES:
        found_any = False
        for frame in page.frames:
            try:
                locator = frame.locator(f"xpath=//*[contains(text(), '{text}')]")
                count = locator.count()
            except PlaywrightError:
                continue
            for i in range(count):
                try:
                    handle = locator.nth(i).element_handle(timeout=2000)
                    if handle is None:
                        continue
                    info = handle.evaluate(EXTRACT_JS)
                except (PlaywrightError, PlaywrightTimeoutError):
                    continue
                info["matched_text"] = text
                info["frame_url"] = frame.url
                info["frame_name"] = frame.name
                info["_frame_ref_index"] = page.frames.index(frame)
                result["candidates"].append(info)
                found_any = True
        if found_any:
            result["matched_text"] = text
            break  # stop at the first candidate text that produced hits
    return result


def score_candidate(c: dict) -> int:
    """Heuristic ranking only - used to suggest a try-order, not to
    silently decide. All candidates are still reported. Visibility is
    weighted heavily: on this portal the real menu link is often inside a
    collapsed tree node (present in the DOM but not clickable without
    first expanding it), while a top-toolbar shortcut to the same
    function is already visible and far more reliable to automate."""
    score = 0
    if c.get("visible"):
        score += 20
    if c.get("tag") in ("a", "button"):
        score += 5
    if c.get("onclick"):
        score += 3
    if c.get("href"):
        score += 2
    if c.get("tag") == "input" and c.get("type") in ("button", "submit", "image"):
        score += 4
    return score


def wait_for_new_frame(page, existing_urls: set, timeout_ms: int = 15000, poll_ms: int = 300):
    """Poll for a frame that did not exist before the click and has
    actually started loading (non-empty, non-blank URL). This portal
    builds its tabs by injecting a new <iframe> via JS after the click,
    so the frame can take a moment to even appear in the DOM, and longer
    still to get a real src - a fixed sleep is not reliable here.
    """
    deadline_steps = max(1, timeout_ms // poll_ms)
    for _ in range(deadline_steps):
        for f in page.frames:
            if f.url and f.url != "about:blank" and f.url not in existing_urls:
                return f
        page.wait_for_timeout(poll_ms)
    return None


def click_and_track(context, page, target_frame, xpath_or_handle, existing_frame_urls=None) -> tuple:
    """Click the trigger element and figure out what happened:
    a new popup Page, or the same Page (possibly a new frame appearing
    inside it, which is how this portal's own JS tab system works).
    """
    existing_frame_urls = existing_frame_urls or {f.url for f in page.frames}
    new_pages = []
    context.on("page", lambda p: new_pages.append(p))

    locator = target_frame.locator(f"xpath={xpath_or_handle}")
    locator.first.scroll_into_view_if_needed(timeout=5000)
    locator.first.click(timeout=10000)
    page.wait_for_timeout(1000)

    if new_pages:
        target = new_pages[0]
        try:
            target.wait_for_load_state("load", timeout=15000)
        except PlaywrightTimeoutError:
            pass
        return target, "popup"

    new_frame = wait_for_new_frame(page, existing_frame_urls)
    if new_frame is not None:
        try:
            new_frame.wait_for_load_state("load", timeout=10000)
        except PlaywrightTimeoutError:
            pass
        try:
            new_frame.wait_for_load_state("networkidle", timeout=8000)
        except PlaywrightTimeoutError:
            pass
        return page, "new_frame_in_same_page"

    try:
        page.wait_for_load_state("networkidle", timeout=8000)
    except PlaywrightTimeoutError:
        pass
    return page, "same_page_or_frame_unconfirmed"


def enumerate_form_elements(target_page) -> list[dict]:
    elements = []
    for frame in target_page.frames:
        for tag in INTERACTIVE_TAGS:
            try:
                handles = frame.query_selector_all(tag)
            except PlaywrightError:
                continue
            for h in handles:
                try:
                    info = h.evaluate(EXTRACT_JS)
                except PlaywrightError:
                    continue
                info["frame_url"] = frame.url
                info["frame_name"] = frame.name
                elements.append(info)
    return elements


def render_element_table(rows: list[dict]) -> str:
    if not rows:
        return "_（未找到任何元素）_\n"
    header = (
        "| tag | type | id | name | label（推測） | text | frame | 建議 selector |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )
    lines = [header]
    for r in rows:
        selector = f"#{r['id']}" if r.get("id") else (
            f"{r['tag']}[name=\"{r['name']}\"]" if r.get("name") else r.get("cssPath", "")
        )
        lines.append(
            "| {tag} | {type} | {id} | {name} | {label} | {text} | {frame} | `{sel}` |\n".format(
                tag=r.get("tag", ""),
                type=r.get("type") or "",
                id=r.get("id") or "",
                name=r.get("name") or "",
                label=(r.get("label") or "").replace("\n", " ")[:30],
                text=(r.get("text") or "").replace("\n", " ")[:30],
                frame=r.get("frame_url", "")[-40:],
                sel=selector,
            )
        )
    return "".join(lines)


def build_markdown(data: dict) -> str:
    md = []
    md.append("# EIP - 出差登記 網站探索分析報告\n")
    md.append(f"\n產出時間：{data['timestamp']}\n")
    md.append(f"\nEIP URL：{data['eip_url']}\n")

    md.append("\n## 1. 首頁結構\n")
    md.append(f"\n- 首頁標題：{data['home_title']}\n")
    md.append(f"- 首頁 URL：{data['home_url']}\n")
    md.append(f"- Frame 數量：{len(data['home_frames'])}\n")
    if len(data['home_frames']) > 1:
        md.append("- **偵測到多個 frame（可能是傳統 frameset 或 iframe 結構）**\n")
    md.append("\n| # | name | url | is_main |\n|---|---|---|---|\n")
    for i, f in enumerate(data['home_frames']):
        md.append(f"| {i} | {f['name'] or ''} | {f['url']} | {f['is_main']} |\n")

    md.append("\n## 2. 「出差登記」觸發元素\n")
    trig = data['trigger']
    if trig['matched_text']:
        md.append(f"\n以文字關鍵字 `{trig['matched_text']}` 找到 {len(trig['candidates'])} 個候選元素"
                   "（依可能性排序，非唯一猜測 - 請人工確認正確項目）：\n\n")
        ranked = sorted(trig['candidates'], key=score_candidate, reverse=True)
        md.append(render_element_table(ranked))
        md.append("\n完整資訊（含 outerHTML / xpath）另存於 `config/selectors.discovered.json`。\n")
    else:
        md.append("\n**未找到任何符合的元素。** 嘗試過的關鍵字："
                   f"{', '.join(TRIGGER_TEXT_CANDIDATES)}。"
                   "可能原因：文字為圖片、iframe 尚未載入、或使用了不同用字，"
                   "請查看 screenshots/ 內的截圖並回報實際畫面文字。\n")

    md.append("\n## 3. 點擊後的行為\n")
    cc = data.get('clicked_candidate')
    if cc:
        md.append(
            f"\n- 實際成功點擊的元素：tag=`{cc['tag']}` id=`{cc.get('id')}` "
            f"frame=`{cc.get('frame_url')}`\n"
        )
        if cc.get("href", "") and cc["href"].startswith("javascript:"):
            md.append(f"- 該元素的 href 是一段 JS 呼叫：`{cc['href']}`\n")
            md.append("  Phase 2 可考慮直接在對應 frame 呼叫這段 JS（例如透過 "
                       "`frame.evaluate(...)`），會比模擬滑鼠點擊一個可能被樹狀選單收合、"
                       "需要先展開才能看到的節點更穩定。\n")
    else:
        md.append("\n- **沒有任何候選元素點擊成功**，請查看 screenshots/03_click_error.png"
                   " 並人工確認正確的觸發方式。\n")
    md.append(f"\n- 偵測結果：**{data['click_mode']}**\n")
    if data['click_mode'] == "popup":
        md.append("  （點擊後開啟了新的瀏覽器視窗/分頁 - Playwright 以 `context.expect_page` 追蹤）\n")
    else:
        md.append("  （沒有新視窗；同一個 Page 內以導覽或 frame 內容更新方式呈現）\n")
    md.append(f"- 表單頁 URL：{data['form_url']}\n")
    md.append(f"- 表單頁 Frame 數量：{len(data['form_frames'])}\n")
    md.append("\n| # | name | url | is_main |\n|---|---|---|---|\n")
    for i, f in enumerate(data['form_frames']):
        md.append(f"| {i} | {f['name'] or ''} | {f['url']} | {f['is_main']} |\n")

    md.append("\n## 4. 出差申請表單欄位清單\n")
    md.append(f"\n共找到 {len(data['form_elements'])} 個 input / select / textarea / button 元素"
               "（跨所有 frame 遞迴掃描）：\n\n")
    md.append(render_element_table(data['form_elements']))

    checkboxes = [e for e in data['form_elements'] if e.get('type') == 'checkbox']
    radios = [e for e in data['form_elements'] if e.get('type') == 'radio']
    selects = [e for e in data['form_elements'] if e.get('tag') == 'select']
    if checkboxes:
        md.append(f"\n### Checkbox（共 {len(checkboxes)}）\n\n")
        md.append(render_element_table(checkboxes))
    if radios:
        md.append(f"\n### Radio（共 {len(radios)}）\n\n")
        md.append(render_element_table(radios))
    if selects:
        md.append(f"\n### Select 選項內容\n\n")
        for s in selects:
            opts = s.get('options') or []
            opt_str = ", ".join(f"{o['text']}({o['value']})" for o in opts[:20])
            md.append(f"- `{s.get('id') or s.get('name') or s.get('cssPath')}`：{opt_str}\n")

    md.append("\n## 5. 截圖清單\n\n")
    for name in data['screenshots']:
        md.append(f"- `screenshots/{name}`\n")

    md.append("\n## 6. Session 保存\n")
    md.append(f"\n- {data.get('session_note', '')}\n")
    md.append("- EIP 要求 Windows 整合驗證（NTLM/Negotiate），Playwright 自行啟動的瀏覽器"
               "無法完成這個驗證且不會顯示原生登入框，因此改用「連線到你手動啟動並登入的 Edge」"
               "（Chrome DevTools Protocol attach）方式，而非 Playwright 產生/保存的 "
               "storage_state 檔案。\n")
    md.append(f"- Edge 使用獨立的 profile 目錄 `{EDGE_PROFILE_DIR}`（已加入 .gitignore），"
               "只要不刪除這個目錄，下次直接照第一步指令重新啟動 Edge，通常不需要再次登入"
               "（除非 session 已在伺服器端過期）。\n")

    md.append("\n## 7. 給 Phase 2 的建議\n")
    md.append("\n- 完整原始資料（含 outerHTML、xpath、cssPath）已寫入 "
               "`config/selectors.discovered.json`，Phase 2 的 `src/trip_form.py` "
               "應以此檔案為主要依據，而非重新猜測 selector。\n")
    md.append("- 若欄位 id 看起來像 ASP.NET WebForms 自動產生的長 id"
               "（例如 `ctl00_ContentPlaceHolder1_txtDate`），優先用 `id` 或 `name` 精確匹配，"
               "避免用文字內容做選擇（文字可能因語系/版本而變動）。\n")
    md.append("- 若表單位於 iframe 或 popup 內，Phase 2 填表前務必先取得對應的 "
               "`Frame`/`Page` 物件，再對該物件操作，不能直接對最外層 `page` 操作。\n")
    md.append("- 送出前所有欄位務必先做「必填檢查」與「內容回顯確認」，"
               "並等待使用者輸入 `y` 才能呼叫送出按鈕，任何情況下都不可自動送出。\n")

    return "".join(md)


def print_edge_launch_instructions():
    EDGE_PROFILE_DIR.mkdir(exist_ok=True)
    print("\n請先手動啟動一個可被自動化連線的 Edge（獨立設定檔，不影響你平常的 Edge）：\n")
    print(f'  & "{EDGE_EXE}" --remote-debugging-port=9222 --user-data-dir="{EDGE_PROFILE_DIR}"\n')
    print("視窗開啟後，請在裡面前往 EIP 並完成登入：")
    print(f"  {EIP_URL}")
    print("確認已經看到登入後的首頁，再回來重新執行本程式：")
    print("  python scripts/inspect_eip.py\n")


def main():
    print(f"EIP URL: {EIP_URL}")
    print(f"嘗試連線到已啟動的 Edge（CDP: {browser_mod.CDP_URL}）...\n")

    with sync_playwright() as pw:
        try:
            br, context = browser_mod.attach_context(pw)
        except browser_mod.CdpConnectionError as e:
            print(f"[error] {e}\n")
            print_edge_launch_instructions()
            return

        page = browser_mod.find_existing_page(context, EIP_URL_FRAGMENT)
        if page is None:
            print(f"[info] 目前沒有開著的 EIP 分頁，開一個新分頁並導向 {EIP_URL} ...")
            page = context.new_page()
            page.goto(EIP_URL, wait_until="domcontentloaded")
        else:
            print(f"[info] 找到現有分頁：{page.url}")

        input(
            "\n>>> 請確認 Edge 視窗中目前是「登入後」的 EIP 首頁，"
            "確認後回到這個終端機按 Enter 繼續... "
        )

        screenshots = [shot(page, "01_home_after_attach.png")]

        home_frames = list_frames(page)
        home_title = page.title()
        home_url = page.url
        print(f"[info] 首頁 frame 數量：{len(home_frames)}")

        print("[info] 搜尋「出差登記」相關元素...")
        trigger = find_trigger_candidates(page)
        print(f"[info] 找到 {len(trigger['candidates'])} 個候選元素（關鍵字：{trigger['matched_text']}）")

        screenshots.append(shot(page, "02_before_click_trip_registration.png"))

        click_mode = "not_attempted"
        form_url = ""
        form_frames = []
        form_elements = []

        clicked_candidate = None
        if trigger["candidates"]:
            ranked = sorted(trigger["candidates"], key=score_candidate, reverse=True)
            existing_frame_urls = {f.url for f in page.frames}
            for candidate in ranked:
                frame_idx = candidate["_frame_ref_index"]
                target_frame = page.frames[frame_idx]
                print(
                    f"[info] 嘗試點擊候選元素：tag={candidate['tag']} id={candidate.get('id')} "
                    f"visible={candidate.get('visible')} text={candidate.get('text')!r}"
                )
                try:
                    target_page, click_mode = click_and_track(
                        context, page, target_frame, candidate["xpath"], existing_frame_urls
                    )
                    form_url = target_page.url
                    form_frames = list_frames(target_page)
                    screenshots.append(shot(target_page, "03_trip_form_page.png"))

                    print("[info] 掃描表單欄位（input/select/textarea/button，跨所有 frame）...")
                    form_elements = enumerate_form_elements(target_page)
                    print(f"[info] 共找到 {len(form_elements)} 個欄位/按鈕元素")
                    clicked_candidate = candidate
                    break
                except (PlaywrightError, PlaywrightTimeoutError) as e:
                    print(f"[warn] 這個候選元素點擊失敗，嘗試下一個：{e}")
            if clicked_candidate is None:
                print("[warn] 所有候選元素都點擊失敗，略過表單頁分析。")
                screenshots.append(shot(page, "03_click_error.png"))
        else:
            print("[warn] 未找到任何「出差登記」候選元素，略過點擊步驟。")

        data = {
            "timestamp": now_str(),
            "eip_url": EIP_URL,
            "home_title": home_title,
            "home_url": home_url,
            "home_frames": home_frames,
            "trigger": trigger,
            "clicked_candidate": clicked_candidate,
            "click_mode": click_mode,
            "form_url": form_url,
            "form_frames": form_frames,
            "form_elements": form_elements,
            "screenshots": screenshots,
            "session_note": (
                "此次分析是連線到你手動啟動並登入的 Edge (CDP attach)，"
                "並非由本程式建立/儲存的 session 檔案。"
            ),
        }

        DISCOVERED_JSON_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[ok] 原始分析資料已寫入 {DISCOVERED_JSON_PATH}")

        DOCS_PATH.write_text(build_markdown(data), encoding="utf-8")
        print(f"[ok] 分析報告已寫入 {DOCS_PATH}")

        print("\n分析完成，未填寫或送出任何表單。")
        print("這是你自己開的 Edge 視窗，本程式不會呼叫任何關閉指令 - 請自行檢查畫面後手動關閉。")
        # Deliberately not calling br.close()/context.close(): this Browser
        # object was obtained via connect_over_cdp() on a real Edge window
        # we did not launch. Closing it here risks killing that whole Edge
        # process (and any other tabs in it), not just detaching.


if __name__ == "__main__":
    main()
