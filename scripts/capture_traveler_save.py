"""Capture browser ground truth for the save-traveler action
(GridUserControl1$Button9).

Answers, from observation rather than inference, what happens between
"ESSF21 is loaded" and "the traveler-save postback has completed":
what JS changes in the DOM, whether CheckPeoplePower fires an AJAX call,
whether the save is a plain submit button or a __doPostBack, what the POST
body actually contains, and whether __MSPVSTATE changes.

ONE-SHOT. Saving a traveler mutates the current draft's server-side state,
so the click is allowed exactly once:
  - A marker file is written BEFORE the click, not after, so even a crash
    mid-click cannot leave the script re-runnable.
  - Re-running afterwards refuses to start. Deleting the marker is a
    deliberate human act, not something this script will ever do.
  - Nothing here retries anything, on any outcome, including UNKNOWN.

Explicitly NOT done here: no MasterPage_btnCreateToolSendForm, no final
send, no draft save, no btClosejQTab, no requests.post, no HTTP replay of
anything captured. src/ is read from but never modified.

Header fields are filled with obvious test data before the traveler code
is entered, because the save button's onclick chain (saveCheckD /
CheckDetailForm / checkRequiredFields_GridUserControl1) may gate on
required fields, and the single allowed click must not be spent on a
validation alert. A pristine snapshot is taken BEFORE that fill, so the
"raw HTML vs JS-executed DOM" comparison stays uncontaminated by typing.

Masking: no real control values ever leave the browser. Values are
fingerprinted in-page with FNV-1a over UTF-8 bytes (crypto.subtle is
unavailable here - EIP is plain HTTP, so the page is not a secure
context), and the identical algorithm is applied in Python to the POST
body, which makes DOM-side and wire-side fingerprints directly
comparable. Only lengths, fingerprints and flags are recorded.

Run (needs a logged-in EIP session, and NO trip form tab already open):
    python scripts/capture_traveler_save.py
"""
import json
import sys
import time
from pathlib import Path
from urllib.parse import parse_qsl

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from playwright.sync_api import sync_playwright  # noqa: E402

import browser as browser_mod  # noqa: E402
import eip_client  # noqa: E402
import webforms_state  # noqa: E402
from dialog_handler import DialogRecorder  # noqa: E402
from session import SessionState, check_session  # noqa: E402

OUT_DIR = ROOT / "logs" / "traveler_save_capture"
MARKER = OUT_DIR / "ALREADY_EXECUTED.marker"

SAVE_BUTTON_ID = "GridUserControl1_Button9"
SAVE_BUTTON_NAME = "GridUserControl1$Button9"
TRAVELER_CODE_ID = "ESSCCDD005_txt"
TRAVELER_NAME_ID = "ESSCCDD006_txt"
FILLER_CODE_ID = "ESSCCDJ004_txt"

# Header test data - obvious dummy values. This only ever lands in a draft;
# nothing in this script submits the application.
TEST_HEADER = {
    "ESSCCDJ024_txt": "2026/01/01",
    "ESSCCDJ025_txt": "09:00",
    "ESSCCDJ026_txt": "2026/01/01",
    "ESSCCDJ027_txt": "18:30",
    "ESSCCDJ028_txt": "Sample location",
    "ESSCCDJ037_txt": "Sample reason",
}

WATCH_FIELDS = [
    "__VIEWSTATE", "__MSPVSTATE", "__MSPVSTATE_ZIP",
    "__EVENTTARGET", "__EVENTARGUMENT", "__TabStrip2_State__",
    "ESSCCDJ023$chk", "ESSCCDJ023_1$chk", "ESSCCDJ038$chk",
    "ESSCCDJ023_hid", "ESSCCDJ023_1_hid", "ESSCCDJ038_hid",
    "GridUserControl1$hdnBtnSaveEnabled",
    "GridUserControl1$hdnGridData", "GridUserControl1$hdnStatus",
    "GridUserControl1$hdnNowIsNew", "GridUserControl1$hdnEditingRow",
    SAVE_BUTTON_NAME, "ESSCCDD005$txt",
]


def fnv1a32(data: bytes) -> str:
    """Non-cryptographic fingerprint, used only to tell "same value" from
    "changed value". Mirrored byte-for-byte by the JS implementation below
    so DOM-side and POST-side fingerprints are comparable."""
    h = 0x811C9DC5
    for b in data:
        h ^= b
        h = (h * 0x01000193) & 0xFFFFFFFF
    return format(h, "08x")


def fp(value: str) -> dict:
    return {"length": len(value), "fnv1a32": fnv1a32(value.encode("utf-8", errors="replace"))}


# --- in-page snapshot -------------------------------------------------
SNAPSHOT_JS = """
(watchNames) => {
  const fnv = (s) => {
    const bytes = new TextEncoder().encode(s);
    let h = 0x811c9dc5;
    for (const b of bytes) {
      h ^= b;
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return ('00000000' + h.toString(16)).slice(-8);
  };

  const form = document.forms['Form1'] || document.forms[0];
  const out = {form_found: !!form, controls: [], form_data: [], watched: {}, grids: []};
  if (!form) return out;

  for (const el of form.elements) {
    const tag = el.tagName.toLowerCase();
    const type = (el.type || '').toLowerCase();
    const v = (el.value === undefined || el.value === null) ? '' : String(el.value);
    out.controls.push({
      tag: tag,
      type: type,
      id: el.id || '',
      name: el.name || '',
      disabled: !!el.disabled,
      checked: (type === 'checkbox' || type === 'radio') ? !!el.checked : null,
      selected_count: tag === 'select' ? (el.selectedOptions ? el.selectedOptions.length : 0) : null,
      value_length: v.length
    });
  }

  // The browser's own computation of successful controls. Submit buttons
  // are correctly absent here - they are contributed by the act of
  // clicking, not by the form's contents.
  try {
    const fd = new FormData(form);
    for (const pair of fd.entries()) {
      const val = typeof pair[1] === 'string' ? pair[1] : '';
      out.form_data.push({name: pair[0], value_length: val.length, fnv1a32: fnv(val)});
    }
  } catch (e) {
    out.form_data_error = String(e);
  }

  for (const n of watchNames) {
    const els = form.elements[n];
    if (!els) { out.watched[n] = null; continue; }
    const el = (els.length !== undefined && !els.tagName) ? els[0] : els;
    const v = (el.value === undefined || el.value === null) ? '' : String(el.value);
    out.watched[n] = {
      present: true,
      length: v.length,
      fnv1a32: fnv(v),
      disabled: !!el.disabled,
      checked: (el.type === 'checkbox' || el.type === 'radio') ? !!el.checked : null,
      tag: el.tagName.toLowerCase(),
      type: (el.type || '').toLowerCase()
    };
  }

  for (const t of document.querySelectorAll('table[id*="Grid"], table[id*="grid"]')) {
    out.grids.push({id: t.id, row_count: t.rows ? t.rows.length : null});
  }
  return out;
}
"""


def snapshot(frame, label: str) -> dict:
    snap = frame.evaluate(SNAPSHOT_JS, WATCH_FIELDS)
    snap["label"] = label
    snap["timestamp"] = time.time()
    return snap


def counts_of(snap: dict) -> dict:
    c = {"named_controls": 0, "disabled": 0, "checked": 0, "form_data_fields": len(snap.get("form_data", []))}
    for ctrl in snap.get("controls", []):
        if ctrl["name"]:
            c["named_controls"] += 1
        if ctrl["disabled"]:
            c["disabled"] += 1
        if ctrl["checked"]:
            c["checked"] += 1
    return c


def diff_snapshots(a: dict, b: dict) -> list:
    """Which named controls changed between two snapshots."""
    def index(snap):
        out = {}
        for ctrl in snap.get("controls", []):
            if ctrl["name"]:
                out.setdefault(ctrl["name"] + "#" + ctrl["id"], ctrl)
        return out

    ia, ib = index(a), index(b)
    changes = []
    for key in sorted(set(ia) | set(ib)):
        ca, cb = ia.get(key), ib.get(key)
        if ca is None:
            changes.append({"key": key, "change": "added", "after": cb})
            continue
        if cb is None:
            changes.append({"key": key, "change": "removed", "before": ca})
            continue
        deltas = {}
        for field in ("disabled", "checked", "value_length"):
            if ca.get(field) != cb.get(field):
                deltas[field] = {"before": ca.get(field), "after": cb.get(field)}
        if deltas:
            changes.append({"key": key, "name": cb["name"], "id": cb["id"], "change": "modified", "deltas": deltas})
    return changes


# --- network recording -----------------------------------------------
class SaveCaptureRecorder:
    """Records requests/responses in enough detail to reconstruct the
    postback, without ever storing a real field value."""

    def __init__(self):
        self.events = []
        self.posts = []
        self.essf21_raw_html = None
        self._page = None
        self._seq = 0

    def _next(self):
        self._seq += 1
        return self._seq

    def _on_request(self, request):
        try:
            headers = request.headers
        except Exception:  # noqa: BLE001
            headers = {}
        entry = {
            "seq": self._next(),
            "kind": "request",
            "timestamp": time.time(),
            "method": request.method,
            "url": request.url.split("?")[0],
            "resource_type": request.resource_type,
            "content_type": headers.get("content-type", ""),
            "is_xhr": request.resource_type in ("xhr", "fetch"),
        }
        if request.method == "POST":
            body = None
            try:
                body = request.post_data
            except Exception:  # noqa: BLE001
                pass
            entry["post"] = self._summarize_post(body, headers)
            self.posts.append(entry)
        self.events.append(entry)

    @staticmethod
    def _summarize_post(body, headers) -> dict:
        if body is None:
            return {"parsed": False, "reason": "post_data unavailable"}
        try:
            pairs = parse_qsl(body, keep_blank_values=True)
        except Exception:  # noqa: BLE001
            return {"parsed": False, "reason": "not parseable as form-encoded", "body_length": len(body)}
        fields = []
        for name, value in pairs:
            item = {"name": name, "value_length": len(value)}
            if name in WATCH_FIELDS:
                item.update(fp(value))
                # Only for the non-sensitive control-flow markers is the
                # literal value itself the answer we're looking for.
                if name in ("__EVENTTARGET", "__EVENTARGUMENT", SAVE_BUTTON_NAME,
                            "GridUserControl1$hdnBtnSaveEnabled", "__MSPVSTATE_ZIP",
                            "ESSCCDJ023$chk", "ESSCCDJ023_1$chk", "ESSCCDJ038$chk",
                            "ESSCCDJ023_hid", "ESSCCDJ023_1_hid", "ESSCCDJ038_hid"):
                    item["value"] = value
            fields.append(item)
        return {
            "parsed": True,
            "body_length": len(body),
            "content_type": headers.get("content-type", ""),
            "content_length_header": headers.get("content-length", ""),
            "field_count": len(fields),
            "field_names": [f["name"] for f in fields],
            "fields": fields,
        }

    def _on_response(self, response):
        try:
            headers = response.headers
        except Exception:  # noqa: BLE001
            headers = {}
        body_len = None
        try:
            body_len = len(response.body())
        except Exception:  # noqa: BLE001
            pass
        entry = {
            "seq": self._next(),
            "kind": "response",
            "timestamp": time.time(),
            "method": response.request.method,
            "url": response.url.split("?")[0],
            "status": response.status,
            "content_type": headers.get("content-type", ""),
            "content_length": headers.get("content-length", ""),
            "body_length": body_len,
            "resource_type": response.request.resource_type,
            "redirect_chain_length": len(response.request.redirected_from.url) if response.request.redirected_from else 0,
        }
        self.events.append(entry)

        if (self.essf21_raw_html is None
                and "ESSF21.aspx" in response.url
                and response.request.method == "GET"
                and response.request.resource_type == "document"):
            try:
                self.essf21_raw_html = response.text()
            except Exception:  # noqa: BLE001
                pass

    def attach(self, page):
        self._page = page
        page.on("request", self._on_request)
        page.on("response", self._on_response)
        return self

    def detach(self):
        if self._page is None:
            return
        self._page.remove_listener("request", self._on_request)
        self._page.remove_listener("response", self._on_response)
        self._page = None

    def ajax_events(self):
        return [e for e in self.events
                if e["kind"] == "request"
                and (e.get("is_xhr") or "ashx" in e["url"].lower() or "ajax" in e["url"].lower())]


def _save(name, obj):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str),
                                encoding="utf-8")


def _wait_for_postback(page, recorder, before_post_count, timeout_s=45) -> bool:
    """Wait for the postback response AND for the frame to finish
    rendering. Deliberately not "the frame url appeared" - that mistake in
    capture_browser_sequence.py captured a half-rendered 1,409-byte page
    when the real response was 144,494 bytes."""
    deadline = time.time() + timeout_s
    saw_post_response = False
    while time.time() < deadline:
        for e in recorder.events:
            if (e["kind"] == "response" and e["method"] == "POST"
                    and "ESSF21.aspx" in e["url"]):
                saw_post_response = True
                break
        if saw_post_response:
            break
        page.wait_for_timeout(300)

    frame = eip_client.find_trip_form_frame(page)
    if frame is not None:
        try:
            frame.wait_for_load_state("load", timeout=15000)
        except Exception:  # noqa: BLE001
            pass
        try:
            frame.wait_for_load_state("networkidle", timeout=15000)
        except Exception:  # noqa: BLE001
            pass

    # Confirm the form is genuinely back before snapshotting.
    while time.time() < deadline:
        frame = eip_client.find_trip_form_frame(page)
        if frame is not None:
            try:
                ready = frame.evaluate(
                    "() => document.readyState === 'complete' && "
                    "!!(document.forms['Form1'] || document.forms[0]) && "
                    "!!((document.forms['Form1'] || document.forms[0]).elements['__MSPVSTATE'])"
                )
                if ready:
                    page.wait_for_timeout(800)  # let trailing JS settle
                    return saw_post_response
            except Exception:  # noqa: BLE001
                pass
        page.wait_for_timeout(300)
    return saw_post_response


def main():
    print("=== Capturing browser ground truth for the save-traveler action ===")
    print("This clicks save exactly once. It never submits the trip application.\n")

    if MARKER.exists():
        print(f"[stop] Found a previous-run marker: {MARKER}")
        print("Saving a traveler mutates the draft's server-side state, so this is "
              "allowed exactly once.")
        print("To capture again - which adds another traveler row - delete that file "
              "by hand first.")
        return 1

    results = {}

    with sync_playwright() as pw:
        try:
            br, context = browser_mod.attach_context(pw)
        except browser_mod.CdpConnectionError as e:
            print(f"[error] {e}")
            return 1

        page = eip_client.open_homepage(context)
        state = check_session(page)
        print(f"Session state: {state.value}")
        if state != SessionState.AUTHENTICATED:
            print("[stop] Not AUTHENTICATED - log in first.")
            return 1

        if eip_client.find_trip_form_frame(page) is not None:
            print("[stop] A trip-registration form is already open.")
            print("This is a one-shot capture, so the form must be brand new and "
                  "untouched.")
            print("Close that tab or reload the EIP homepage, then run this again.")
            return 1

        recorder = SaveCaptureRecorder().attach(page)
        dialogs = DialogRecorder().attach(page)

        try:
            # --- open a fresh form ---------------------------------
            print("\n[1] Opening a fresh trip-registration form...")
            eip_client.open_trip_form(page)
            frame = eip_client.find_trip_form_frame(page)
            if frame is None:
                print("[stop] ESSF21 frame not found.")
                return 1
            page.wait_for_timeout(1500)
            print(f"    Form loaded. Raw HTML captured: "
                  f"{bool(recorder.essf21_raw_html)}")

            # --- SNAPSHOT A: pristine ------------------------------
            print("\n[2] Snapshot A: the DOM after JS ran but before any input - the "
                  "baseline for comparing against the raw HTML")
            snap_a = snapshot(frame, "A_pristine_dom")
            results["snapshot_a_pristine"] = snap_a
            print(f"    named controls: {counts_of(snap_a)['named_controls']}, "
                  f"FormData fields: {counts_of(snap_a)['form_data_fields']}")

            raw_form = None
            if recorder.essf21_raw_html:
                raw_form = webforms_state.parse_form(recorder.essf21_raw_html)
                results["raw_html_counts"] = raw_form.counts()
                (OUT_DIR / "essf21_raw.html").parent.mkdir(parents=True, exist_ok=True)
                (OUT_DIR / "essf21_raw.html").write_text(recorder.essf21_raw_html,
                                                         encoding="utf-8", errors="replace")
                print(f"    raw HTML successful controls：{raw_form.counts()['successful_controls']}")

                print("\n    --- raw HTML vs browser DOM (checkboxes specifically) ---")
                cmp_rows = []
                for cb_id, cb_name in (("ESSCCDJ023_chk", "ESSCCDJ023$chk"),
                                       ("ESSCCDJ023_1_chk", "ESSCCDJ023_1$chk"),
                                       ("ESSCCDJ038_chk", "ESSCCDJ038$chk")):
                    raw_ctrl = raw_form.by_id(cb_id)
                    dom_ctrl = next((c for c in snap_a["controls"] if c["id"] == cb_id), None)
                    row = {
                        "id": cb_id,
                        "name": cb_name,
                        "raw_html_checked": raw_ctrl.checked if raw_ctrl else None,
                        "browser_dom_checked": dom_ctrl["checked"] if dom_ctrl else None,
                    }
                    row["differs"] = row["raw_html_checked"] != row["browser_dom_checked"]
                    cmp_rows.append(row)
                    print(f"      {cb_id:20s} raw={row['raw_html_checked']}  "
                          f"DOM={row['browser_dom_checked']}  "
                          f"{'*** MISMATCH ***' if row['differs'] else 'match'}")
                results["checkbox_raw_vs_dom"] = cmp_rows

            # --- fill header ---------------------------------------
            print("\n[3] Filling header fields with test data, so the single allowed "
                  "click is not spent on a validation alert")
            for fid, val in TEST_HEADER.items():
                try:
                    frame.fill(f"#{fid}", val)
                except Exception as e:  # noqa: BLE001
                    print(f"    [warn] Could not fill {fid}: {e}")
            page.wait_for_timeout(800)
            snap_a2 = snapshot(frame, "A2_header_filled")
            results["snapshot_a2_header_filled"] = snap_a2

            # --- enter traveler code -------------------------------
            filler_code = frame.input_value(f"#{FILLER_CODE_ID}")
            print(f"\n[4] Entering the traveler code - the logged-in user's own employee "
                  f"code, length {len(filler_code)}")
            posts_before_validation = len(recorder.posts)
            ajax_before = len(recorder.ajax_events())

            code_locator = frame.locator(f"#{TRAVELER_CODE_ID}")
            code_locator.fill(filler_code)
            code_locator.press("Tab")
            page.wait_for_timeout(2500)  # let onblur / CheckPeoplePower finish

            resolved_name = frame.input_value(f"#{TRAVELER_NAME_ID}")
            print(f"    resolved name length after validation: {len(resolved_name)} "
                  f"({'name resolved' if resolved_name else 'empty - validation may have failed'})")

            ajax_during = recorder.ajax_events()[ajax_before:]
            results["validation_ajax"] = ajax_during
            print(f"    XHR/AJAX/ashx requests during validation: {len(ajax_during)}")
            for e in ajax_during:
                print(f"      {e['method']} {e['url']}  type={e['resource_type']}"
                      f"  content-type={e['content_type']}")
            new_posts = recorder.posts[posts_before_validation:]
            results["validation_posts"] = new_posts
            print(f"    POST requests during validation: {len(new_posts)}"
                  f"{' - so the AJAX may create or change server state' if new_posts else ''}")

            # --- SNAPSHOT B ----------------------------------------
            print("\n[5] Snapshot B: after validation completed")
            snap_b = snapshot(frame, "B_after_validation")
            results["snapshot_b_after_validation"] = snap_b
            changes = diff_snapshots(snap_a2, snap_b)
            results["diff_a2_to_b"] = changes
            print(f"    controls JavaScript changed since snapshot A2: {len(changes)}")
            for ch in changes[:40]:
                if ch["change"] == "modified":
                    print(f"      {ch['name']} (id={ch['id']}): {ch['deltas']}")
                else:
                    print(f"      {ch['change']}: {ch['key']}")

            btn_a2 = snap_a2["watched"].get(SAVE_BUTTON_NAME)
            btn_b = snap_b["watched"].get(SAVE_BUTTON_NAME)
            en_a2 = snap_a2["watched"].get("GridUserControl1$hdnBtnSaveEnabled")
            en_b = snap_b["watched"].get("GridUserControl1$hdnBtnSaveEnabled")
            print(f"\n    Button9 disabled: {btn_a2 and btn_a2['disabled']} -> {btn_b and btn_b['disabled']}")
            print(f"    hdnBtnSaveEnabled fingerprint: "
                  f"{en_a2 and en_a2['fnv1a32']} -> {en_b and en_b['fnv1a32']}"
                  f"  (length {en_a2 and en_a2['length']} -> {en_b and en_b['length']})")

            # --- SNAPSHOT C: final pre-click ------------------------
            print("\n[6] Snapshot C: the last instant before clicking, using the "
                  "browser's own FormData")
            snap_c = snapshot(frame, "C_final_pre_click")
            results["snapshot_c_pre_click"] = snap_c
            c_counts = counts_of(snap_c)
            print(f"    FormData successful controls: {c_counts['form_data_fields']}")
            print(f"    named {c_counts['named_controls']}, disabled {c_counts['disabled']}, "
                  f"checked {c_counts['checked']}")

            if raw_form is not None:
                dom_names = [f["name"] for f in snap_c["form_data"]]
                raw_names = [n for n, _ in raw_form.successful_controls()]
                results["diff_raw_vs_dom_successful"] = {
                    "raw_count": len(raw_names),
                    "dom_count": len(dom_names),
                    "only_in_raw": sorted(set(raw_names) - set(dom_names)),
                    "only_in_dom": sorted(set(dom_names) - set(raw_names)),
                }
                print(f"    vs the raw-HTML payload: raw {len(raw_names)} vs DOM {len(dom_names)}")
                print(f"      only in raw: {sorted(set(raw_names) - set(dom_names))}")
                print(f"      only in DOM: {sorted(set(dom_names) - set(raw_names))}")

            btn_state = snap_c["watched"].get(SAVE_BUTTON_NAME)
            if btn_state and btn_state["disabled"]:
                print("\n[stop] The save button is still disabled, so clicking it would "
                      "do nothing.")
                print("Stopping without clicking, so the single allowed click is not wasted.")
                _save("results_partial.json", results)
                return 1

            # --- THE ONE CLICK --------------------------------------
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            MARKER.write_text(
                f"Save-traveler was executed once at {time.strftime('%Y-%m-%d %H:%M:%S')}.\n"
                "This file is written BEFORE the click, so a crash mid-click still cannot\n"
                "leave the script re-runnable.\n"
                "Capturing again requires deleting this file by hand, and understanding\n"
                "that it will add another traveler row.\n",
                encoding="utf-8",
            )
            print("\n[7] *** Performing the single allowed save-traveler click ***")
            posts_before = len(recorder.posts)
            frame.click(f"#{SAVE_BUTTON_ID}", timeout=10000)

            ok = _wait_for_postback(page, recorder, posts_before, timeout_s=45)
            print(f"    POST response received: {'yes' if ok else 'no (timed out)'}")

            # --- POST body ------------------------------------------
            save_posts = recorder.posts[posts_before:]
            results["save_posts"] = save_posts
            print(f"\n[8] POST requests captured: {len(save_posts)}")
            for p in save_posts:
                post = p.get("post", {})
                print(f"    {p['method']} {p['url']}")
                print(f"      Content-Type: {post.get('content_type')}")
                print(f"      Content-Length: {post.get('content_length_header')}"
                      f"  actual body length: {post.get('body_length')}")
                print(f"      field count: {post.get('field_count')}")
                if post.get("parsed"):
                    interesting = {f["name"]: f for f in post["fields"] if f["name"] in WATCH_FIELDS}
                    print("      fields of interest:")
                    for name in WATCH_FIELDS:
                        f = interesting.get(name)
                        if f is None:
                            print(f"        {name:38s} not in the POST body")
                        elif "value" in f:
                            print(f"        {name:38s} value={f['value']!r} (len={f['value_length']})")
                        else:
                            print(f"        {name:38s} len={f['value_length']} fnv={f.get('fnv1a32')}")

            # --- SNAPSHOT D -----------------------------------------
            print("\n[9] Snapshot D: after the POST completed")
            frame = eip_client.find_trip_form_frame(page)
            if frame is None:
                print("    [warn] No ESSF21 frame after the POST, so snapshot D is unavailable.")
                results["snapshot_d_after_post"] = None
            else:
                snap_d = snapshot(frame, "D_after_post")
                results["snapshot_d_after_post"] = snap_d
                for name in ("__MSPVSTATE", "__MSPVSTATE_ZIP", "__EVENTTARGET",
                             "__EVENTARGUMENT", "GridUserControl1$hdnBtnSaveEnabled"):
                    b = snap_c["watched"].get(name)
                    d = snap_d["watched"].get(name)
                    if b and d:
                        changed = b["fnv1a32"] != d["fnv1a32"]
                        print(f"    {name:38s} len {b['length']} -> {d['length']}  "
                              f"{'*** CHANGED ***' if changed else 'unchanged'}")
                print("\n    grid row-count changes:")
                gb = {g["id"]: g["row_count"] for g in snap_c.get("grids", [])}
                gd = {g["id"]: g["row_count"] for g in snap_d.get("grids", [])}
                for gid in sorted(set(gb) | set(gd)):
                    before, after = gb.get(gid), gd.get(gid)
                    mark = " <== row added" if (before is not None and after is not None and after > before) else ""
                    print(f"      {gid}: {before} -> {after}{mark}")
                results["grid_before"] = gb
                results["grid_after"] = gd

            results["dialogs"] = [
                {"type": d.dialog_type, "message": d.message, "action": d.action}
                for d in dialogs.events
            ]
            if dialogs.events:
                print(f"\n    dialogs captured: {len(dialogs.events)}")
                for d in dialogs.events:
                    print(f"      [{d.dialog_type}] {d.action}: {d.message}")

        finally:
            dialogs.detach()
            recorder.detach()
            results["all_events"] = recorder.events
            _save("results.json", results)
            print(f"\nFull results written to {OUT_DIR / 'results.json'}")

    print("\n=== Done. No trip application was submitted, and no HTTP POST was replayed. ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
