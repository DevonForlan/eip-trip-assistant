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
     trip-registration element by inspecting real DOM text/attributes - it does
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
# 15+ year old ASP.NET portal might not use exactly the expected wording - all
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
        return "_(no elements found)_\n"
    header = (
        "| tag | type | id | name | label (guessed) | text | frame | suggested selector |\n"
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
    md.append("# EIP trip-registration - site exploration report\n")
    md.append(f"\nGenerated: {data['timestamp']}\n")
    md.append(f"\nEIP URL：{data['eip_url']}\n")

    md.append("\n## 1. Homepage structure\n")
    md.append(f"\n- Title: {data['home_title']}\n")
    md.append(f"- URL: {data['home_url']}\n")
    md.append(f"- Frame count: {len(data['home_frames'])}\n")
    if len(data['home_frames']) > 1:
        md.append("- **Multiple frames detected (a classic frameset or nested iframes)**\n")
    md.append("\n| # | name | url | is_main |\n|---|---|---|---|\n")
    for i, f in enumerate(data['home_frames']):
        md.append(f"| {i} | {f['name'] or ''} | {f['url']} | {f['is_main']} |\n")

    md.append("\n## 2. The trip-registration trigger element\n")
    trig = data['trigger']
    if trig['matched_text']:
        md.append(f"\nSearching for the text `{trig['matched_text']}` found "
                  f"{len(trig['candidates'])} candidate elements, ranked by likelihood. "
                  "These are candidates, not a single guess - confirm the right one by hand:\n\n")
        ranked = sorted(trig['candidates'], key=score_candidate, reverse=True)
        md.append(render_element_table(ranked))
        md.append("\nFull detail (including outerHTML / xpath) is written to "
                  "`config/selectors.discovered.json`.\n")
    else:
        md.append("\n**No matching element found.** Keywords tried: "
                   f"{', '.join(TRIGGER_TEXT_CANDIDATES)}。"
                  "Possible causes: the label is an image, the iframe had not loaded yet, "
                  "or the wording differs. Check the screenshots in screenshots/ and report "
                  "the actual on-screen text.\n")

    md.append("\n## 3. What happens on click\n")
    cc = data.get('clicked_candidate')
    if cc:
        md.append(
            f"\n- The element that was actually clicked: tag=`{cc['tag']}` id=`{cc.get('id')}` "
            f"frame=`{cc.get('frame_url')}`\n"
        )
        if cc.get("href", "") and cc["href"].startswith("javascript:"):
            md.append(f"- Its href is a JS call: `{cc['href']}`\n")
            md.append("  Calling that JS directly in the owning frame (via "
                      "`frame.evaluate(...)`) is more robust than clicking a node that may "
                      "be collapsed inside the sidebar tree and need expanding first.\n")
    else:
        md.append("\n- **No candidate could be clicked successfully.** See "
                  "screenshots/03_click_error.png and confirm the correct trigger by hand.\n")
    md.append(f"\n- Detected mode: **{data['click_mode']}**\n")
    if data['click_mode'] == "popup":
        md.append("  (The click opened a new window/tab - tracked via `context.expect_page`.)\n")
    else:
        md.append("  (No new window; the same Page either navigated or updated frame content.)\n")
    md.append(f"- Form page URL: {data['form_url']}\n")
    md.append(f"- Form page frame count: {len(data['form_frames'])}\n")
    md.append("\n| # | name | url | is_main |\n|---|---|---|---|\n")
    for i, f in enumerate(data['form_frames']):
        md.append(f"| {i} | {f['name'] or ''} | {f['url']} | {f['is_main']} |\n")

    md.append("\n## 4. Form fields\n")
    md.append(f"\n{len(data['form_elements'])} input / select / textarea / button elements "
              "found, scanning all frames recursively:\n\n")
    md.append(render_element_table(data['form_elements']))

    checkboxes = [e for e in data['form_elements'] if e.get('type') == 'checkbox']
    radios = [e for e in data['form_elements'] if e.get('type') == 'radio']
    selects = [e for e in data['form_elements'] if e.get('tag') == 'select']
    if checkboxes:
        md.append(f"\n### Checkboxes ({len(checkboxes)})\n\n")
        md.append(render_element_table(checkboxes))
    if radios:
        md.append(f"\n### Radios ({len(radios)})\n\n")
        md.append(render_element_table(radios))
    if selects:
        md.append("\n### Select options\n\n")
        for s in selects:
            opts = s.get('options') or []
            opt_str = ", ".join(f"{o['text']}({o['value']})" for o in opts[:20])
            md.append(f"- `{s.get('id') or s.get('name') or s.get('cssPath')}`：{opt_str}\n")

    md.append("\n## 5. Screenshots\n\n")
    for name in data['screenshots']:
        md.append(f"- `screenshots/{name}`\n")

    md.append("\n## 6. Session handling\n")
    md.append(f"\n- {data.get('session_note', '')}\n")
    md.append("- EIP requires Windows Integrated Authentication (NTLM/Negotiate). A browser "
              "Playwright launches itself cannot complete that handshake and surfaces no "
              "native credential prompt, so this attaches over the Chrome DevTools Protocol "
              "to an Edge that is already logged in, rather than using a Playwright-managed "
              "storage_state file.\n")
    md.append(f"- Edge uses its own profile directory `{EDGE_PROFILE_DIR}` (gitignored). "
              "As long as that directory survives, relaunching Edge with the same command "
              "usually needs no fresh login, unless the server-side session has expired.\n")

    md.append("\n## 7. Notes for building the automation\n")
    md.append("\n- The full raw data (outerHTML, xpath, cssPath) is written to "
              "`config/selectors.discovered.json`. Base `src/trip_form.py` on that file "
              "rather than guessing selectors again.\n")
    md.append("- Where ids look like ASP.NET WebForms generated names (e.g. "
              "`ctl00_ContentPlaceHolder1_txtDate`), match exactly on `id` or `name` rather "
              "than on visible text, which can shift with locale or version.\n")
    md.append("- When the form lives in an iframe or popup, obtain that `Frame`/`Page` "
              "object first and operate on it - never on the outermost `page`.\n")
    md.append("- Before sending, always check required fields and read the values back from "
              "the live page for the user to confirm. Only call the send button after an "
              "explicit `y`; never send automatically.\n")

    return "".join(md)


def print_edge_launch_instructions():
    EDGE_PROFILE_DIR.mkdir(exist_ok=True)
    print("\nLaunch an automation-attachable Edge first. It uses its own profile, so your "
          "everyday Edge is unaffected:\n")
    print(f'  & "{EDGE_EXE}" --remote-debugging-port=9222 --user-data-dir="{EDGE_PROFILE_DIR}"\n')
    print("Once the window opens, go to EIP in it and log in:")
    print(f"  {EIP_URL}")
    print("Confirm you can see the logged-in homepage, then run this program again:")
    print("  python scripts/inspect_eip.py\n")


def main():
    print(f"EIP URL: {EIP_URL}")
    print(f"Connecting to the running Edge (CDP: {browser_mod.CDP_URL})...\n")

    with sync_playwright() as pw:
        try:
            br, context = browser_mod.attach_context(pw)
        except browser_mod.CdpConnectionError as e:
            print(f"[error] {e}\n")
            print_edge_launch_instructions()
            return

        page = browser_mod.find_existing_page(context, EIP_URL_FRAGMENT)
        if page is None:
            print(f"[info] No EIP tab is open; opening a new tab at {EIP_URL} ...")
            page = context.new_page()
            page.goto(EIP_URL, wait_until="domcontentloaded")
        else:
            print(f"[info] Found an existing tab: {page.url}")

        input(
            "\n>>> Confirm the Edge window is showing the logged-in EIP homepage, "
            "then come back here and press Enter to continue... "
        )

        screenshots = [shot(page, "01_home_after_attach.png")]

        home_frames = list_frames(page)
        home_title = page.title()
        home_url = page.url
        print(f"[info] Homepage frame count: {len(home_frames)}")

        print("[info] Searching for the trip-registration element...")
        trigger = find_trigger_candidates(page)
        print(f"[info] Found {len(trigger['candidates'])} candidates "
              f"(keyword: {trigger['matched_text']})")

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
                    f"[info] Trying candidate: tag={candidate['tag']} id={candidate.get('id')} "
                    f"visible={candidate.get('visible')} text={candidate.get('text')!r}"
                )
                try:
                    target_page, click_mode = click_and_track(
                        context, page, target_frame, candidate["xpath"], existing_frame_urls
                    )
                    form_url = target_page.url
                    form_frames = list_frames(target_page)
                    screenshots.append(shot(target_page, "03_trip_form_page.png"))

                    print("[info] Scanning form fields (input/select/textarea/button, all frames)...")
                    form_elements = enumerate_form_elements(target_page)
                    print(f"[info] Found {len(form_elements)} field/button elements")
                    clicked_candidate = candidate
                    break
                except (PlaywrightError, PlaywrightTimeoutError) as e:
                    print(f"[warn] That candidate could not be clicked; trying the next: {e}")
            if clicked_candidate is None:
                print("[warn] No candidate could be clicked; skipping form-page analysis.")
                screenshots.append(shot(page, "03_click_error.png"))
        else:
            print("[warn] No trip-registration candidate found; skipping the click step.")

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
                "This analysis attached over CDP to an Edge the user launched and logged "
                "into; no session file is created or stored by this program."
            ),
        }

        DISCOVERED_JSON_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[ok] Raw analysis data written to {DISCOVERED_JSON_PATH}")

        DOCS_PATH.write_text(build_markdown(data), encoding="utf-8")
        print(f"[ok] Report written to {DOCS_PATH}")

        print("\nAnalysis complete. No form was filled in or submitted.")
        print("This is your own Edge window - this program never closes it. Inspect the "
              "screen and close it yourself when done.")
        # Deliberately not calling br.close()/context.close(): this Browser
        # object was obtained via connect_over_cdp() on a real Edge window
        # we did not launch. Closing it here risks killing that whole Edge
        # process (and any other tabs in it), not just detaching.


if __name__ == "__main__":
    main()
