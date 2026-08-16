"""Cumulative fresh-session ladder: what flips EPIE001 from 15,275 bytes
to the ~90-100KB full version? GET-only, independent POC.

Background. Three observations that this script is built to reconcile:
  1. The ONE successful pure-HTTP run (docs/http-webforms-poc.md) had
     crawled the EFNET frame tree in the SAME session before it hit
     EPIE001.
  2. A later probe that went straight to TreeMainFrame.aspx and then
     EPIE001 failed - so TreeMainFrame alone is evidently not enough.
  3. /EFNET/'s own frame src is CollectData.aspx (which redirects to
     TreeMainFrame.aspx) - observed in logs/http_explorer/findings.json.
     The failing probe skipped CollectData.aspx entirely.

So the hypothesis under test is "requests never went through EFNET's
browser initialization", not "user-level single tab lock".

Design rule this script exists to enforce: GET EPIE001 may itself mutate
server-side state, so every rung of the ladder is a BRAND NEW
requests.Session() that issues EXACTLY ONE EPIE001 GET, as its last
request. Never "session -> EPIE001 -> add a step -> EPIE001 again".

URL provenance - nothing here is guessed:
  - The initialization ASPX URLs come from docs/eip-analysis.md section 1
    (the live frame table captured from a real logged-in session) and
    from logs/http_explorer/findings.json (CollectData.aspx).
  - EPIE001_REFERER is the literal value the real browser sent, read out
    of logs/browser_capture/sequence.json seq=1. Note that
    logs/browser_capture/sequence.json does NOT contain the pre-click
    frameset loads (the recorder attached at click time, when the shell
    was already loaded), which is exactly why the init URLs above are
    sourced from the other two files instead.

Scope limits:
  - GET only. Grep this file for ".post(" to verify rather than trusting
    this comment.
  - Rung S5 includes a GET of the PARAMETERLESS ESSF21.aspx path, purely
    because the one known-successful run happened to do that (it 302s
    straight to HRMESS's SessionTimeOut.aspx - no Identifier, no form
    data, nothing readable). That is not "fetching the form", and this
    script never GETs an ESSF21 URL carrying an Identifier.
  - Stops at the first rung that yields the full version, and does NOT
    follow up by fetching ESSF21, per the current instructions.
  - Touches nothing in src/.

Masking: cookie NAMES only (never values); Authorization never read;
EPIE001 bodies are hashed (sha256, first 12 hex) rather than quoted, and
full bodies land in logs/http_epie001_init_ab_test/ (gitignored) for
offline human inspection only.

Run:
    python scripts/http_epie001_init_ab_test.py
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import requests
    from dotenv import load_dotenv
    from requests_negotiate_sspi import HttpNegotiateAuth
except ImportError as e:  # noqa: BLE001
    print(f"[error] 缺少必要套件，請先執行 pip install -r requirements.txt（{e}）")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "logs" / "http_epie001_init_ab_test"

load_dotenv(ROOT / ".env")

HOST = os.environ.get("EIP_URL", "http://eip.example.com/EFNET/") \
    .split("//", 1)[-1].split("/", 1)[0].split(":", 1)[0]
FRAMESET = f"http://{HOST}/EFNET/src/_Common/AppUtil/FrameSet"

EFNET = f"http://{HOST}/EFNET/"
COLLECT_DATA = f"{FRAMESET}/CollectData.aspx"
TREE_MAIN_FRAME = f"{FRAMESET}/TreeMainFrame.aspx"
TITLEBAR = f"{FRAMESET}/titlebar1.aspx"
TREE = f"{FRAMESET}/tree.aspx"
MARQUEE = f"{FRAMESET}/Marquee.aspx"
PLATFORM = f"{FRAMESET}/platform.aspx"
MAIN = f"{FRAMESET}/main.aspx"
HOME_TAB = f"{FRAMESET}/HomeTab.aspx"
SHOW_STATUS = f"{FRAMESET}/ShowStatus.aspx"
BARE_ESSF21 = f"http://{HOST}/HRMESS/src/ESS/ESSF21/ESSF21.aspx"

EPIE001 = f"http://{HOST}/EFNET/src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21"
EPIE001_REFERER = PLATFORM  # literal value the real browser sent (capture seq=1)

# Raised from 20s after observing the full-version path transiently block:
# it returned in 3,687ms, then exceeded 20s three times in a row, then
# returned in 0.4s. A 20s ceiling conflates "transiently blocked" with
# "server deliberately answered with the slim version" - and those two
# mean completely different things here, since the slim answer always
# comes back fast and byte-identical.
TIMEOUT_SECONDS = 60
FULL_VERSION_MIN_BYTES = 50_000  # known: slim=15,275 / full=91,694~98,484
EPIE001_MARKERS = ["framePlus", "ESSF21.aspx", "Identifier", "hdnplusFrameUrl"]

# Each rung: (id, description, [init urls...], referer_for_epie001 or None)
LADDER = [
    ("S0", "Minimal（Experiment 1）：只 GET 首頁就打 EPIE001", [EFNET], None),
    ("S1", "Experiment 2：首頁 → TreeMainFrame（直接打，跳過 CollectData）", [EFNET, TREE_MAIN_FRAME], None),
    ("S2", "隔離 CollectData：首頁 → CollectData（自動轉往 TreeMainFrame）", [EFNET, COLLECT_DATA], None),
    ("S3", "＋ tree", [EFNET, COLLECT_DATA, TREE], None),
    ("S4", "＋ Marquee ＋ ShowStatus（＝當初 explorer 爬 frame 的範圍）",
     [EFNET, COLLECT_DATA, TREE, MARQUEE, SHOW_STATUS], None),
    ("S5", "＋ 裸 ESSF21（＝唯一成功過那次的完整重播）",
     [EFNET, COLLECT_DATA, TREE, MARQUEE, SHOW_STATUS, BARE_ESSF21], None),
    ("S6", "Experiment 3：Browser-like 完整初始化（無 Referer）",
     [EFNET, COLLECT_DATA, TITLEBAR, TREE, MARQUEE, PLATFORM, MAIN, HOME_TAB, SHOW_STATUS], None),
    ("S7", "Experiment 3：Browser-like 完整初始化 ＋ Referer=platform.aspx",
     [EFNET, COLLECT_DATA, TITLEBAR, TREE, MARQUEE, PLATFORM, MAIN, HOME_TAB, SHOW_STATUS], EPIE001_REFERER),
]

SESSION_COOKIE = "ASP.NET_SessionId"


def _cookie_names(session) -> list:
    return sorted({c.name for c in session.cookies})


def _short_url(url: str) -> str:
    return url.replace(f"http://{HOST}", "").replace("/EFNET/src/_Common/AppUtil/FrameSet", "…/FrameSet")


def _do_get(session, url: str, referer: str | None = None) -> dict:
    names_before = _cookie_names(session)
    step = {
        "url": url,
        "short_url": _short_url(url),
        "referer_sent": referer or "",
        "cookie_names_before": names_before,
        "sessionid_present_before": SESSION_COOKIE in names_before,
    }
    headers = {"Referer": referer} if referer else {}
    t0 = time.monotonic()
    try:
        resp = session.get(url, timeout=TIMEOUT_SECONDS, headers=headers, allow_redirects=True)
    except requests.RequestException as e:
        step["error"] = str(e)
        step["elapsed_ms"] = round((time.monotonic() - t0) * 1000, 1)
        return step, None
    step["elapsed_ms"] = round((time.monotonic() - t0) * 1000, 1)

    names_after = _cookie_names(session)
    step.update(
        {
            "status": resp.status_code,
            "final_short_url": _short_url(resp.url),
            "body_bytes": len(resp.content),
            "content_type": resp.headers.get("Content-Type", ""),
            "redirected": bool(resp.history),
            "cookie_names_after": names_after,
            "sessionid_present_after": SESSION_COOKIE in names_after,
            "new_cookie_names": sorted(set(names_after) - set(names_before)),
        }
    )
    return step, resp


def run_rung(rung_id: str, description: str, init_urls: list, referer: str | None) -> dict:
    print(f"\n{'=' * 70}\n{rung_id}: {description}\n{'=' * 70}")
    result = {"rung": rung_id, "description": description, "referer_on_epie001": referer or "", "steps": []}

    session = requests.Session()
    session.auth = HttpNegotiateAuth()

    for url in init_urls:
        step, resp = _do_get(session, url)
        result["steps"].append(step)
        if "error" in step:
            print(f"  [error] GET {step['short_url']} -> {step['error']}")
            result["outcome"] = "INIT_STEP_FAILED"
            return result
        flag = "  <== 這一步產生了 SessionId" if (
            step["sessionid_present_after"] and not step["sessionid_present_before"]
        ) else ""
        print(f"  GET {step['short_url']:44s} {step['status']} {step['body_bytes']:>8,}B "
              f"sid={'Y' if step['sessionid_present_after'] else 'N'}{flag}")

    epie_step, resp = _do_get(session, EPIE001, referer=referer)
    result["steps"].append(epie_step)
    if "error" in epie_step:
        print(f"  [error] GET EPIE001 -> {epie_step['error']}")
        result["outcome"] = "EPIE001_FAILED"
        return result

    body = resp.content
    text = body.decode("utf-8", errors="replace")
    digest12 = hashlib.sha256(body).hexdigest()[:12]
    markers = {m: (m in text) for m in EPIE001_MARKERS}

    result["epie001"] = {
        "status": resp.status_code,
        "body_bytes": len(body),
        "sha256_prefix12": digest12,
        "markers": markers,
        "sessionid_present": epie_step["sessionid_present_after"],
        "cookie_names": epie_step["cookie_names_after"],
        "referer_sent": referer or "",
    }
    is_full = len(body) >= FULL_VERSION_MIN_BYTES and markers["ESSF21.aspx"]
    result["outcome"] = "FULL" if is_full else "SLIM"

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"epie001_{rung_id}.html").write_text(text, encoding="utf-8", errors="replace")

    print(f"  GET {'EPIE001.aspx?FormID=ESSF21':44s} {resp.status_code} {len(body):>8,}B "
          f"sha256[:12]={digest12}")
    print(f"      markers: {markers}")
    print(f"      >>> {result['outcome']}"
          f"{'  <<<<<< 完整版出現！' if is_full else '（精簡版）'}")
    return result


def confirm_mode():
    """Interleaved reproducibility check, run as:
        python scripts/http_epie001_init_ab_test.py confirm

    The ladder above runs strictly ascending, so a lone success at S2
    could in principle be a temporal artifact ("whatever was blocking
    S0/S1 happened to clear by the time S2 ran") rather than
    CollectData.aspx actually being the cause. Interleaving S2 with
    S0/S1 - and starting with S2 - breaks that confound: if the cause is
    CollectData, every S2 is FULL and every S0/S1 is SLIM regardless of
    position; if it were timing, the pattern would follow position
    instead.

    Still GET-only, still one EPIE001 per fresh session, still never
    touches an ESSF21 URL carrying an Identifier.
    """
    by_id = {r[0]: r for r in LADDER}
    order = ["S2", "S0", "S2", "S1", "S2"]
    print("交錯重現測試（刻意從 S2 開始，用來排除「只是時間點剛好」這個可能）")
    print(f"順序：{' → '.join(order)}\n")

    results = []
    for n, rung_id in enumerate(order, start=1):
        _, description, init_urls, referer = by_id[rung_id]
        r = run_rung(f"{rung_id}#{n}", f"[重現測試 第{n}輪] {description}", init_urls, referer)
        r["base_rung"] = rung_id
        results.append(r)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "confirm_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    print(f"\n{'=' * 70}\n重現測試總結\n{'=' * 70}")
    print(f"{'#':3s} {'Rung':6s} {'Outcome':8s} {'Bytes':>10s}  sha256[:12]")
    for n, r in enumerate(results, start=1):
        e = r.get("epie001")
        if e is None:
            print(f"{n:<3d} {r['base_rung']:6s} {r.get('outcome', '?'):8s} {'-':>10s}  -")
            continue
        print(f"{n:<3d} {r['base_rung']:6s} {r['outcome']:8s} {e['body_bytes']:>10,}  {e['sha256_prefix12']}")

    s2 = [r for r in results if r["base_rung"] == "S2" and r.get("epie001")]
    others = [r for r in results if r["base_rung"] in ("S0", "S1") and r.get("epie001")]
    s2_all_full = bool(s2) and all(r["outcome"] == "FULL" for r in s2)
    others_all_slim = bool(others) and all(r["outcome"] == "SLIM" for r in others)

    if s2_all_full and others_all_slim:
        verdict = "CONFIRMED_COLLECTDATA_IS_THE_TRIGGER"
        msg = (f"S2（走 CollectData）{len(s2)}/{len(s2)} 全部完整版，"
               f"S0/S1（沒走 CollectData）{len(others)}/{len(others)} 全部精簡版，"
               "且順序刻意打亂 - CollectData.aspx 就是切換條件，不是時間點造成的。")
    elif s2_all_full:
        verdict = "PARTIAL"
        msg = "S2 全部成功，但 S0/S1 不是全部精簡版，需要再看細節。"
    else:
        verdict = "NOT_REPRODUCIBLE"
        msg = "S2 沒有穩定重現，先前那次成功可能仍受其他因素影響，不可下結論。"

    print(f"\n判定：{verdict}\n理由：{msg}")
    (OUT_DIR / "confirm_verdict.json").write_text(
        json.dumps({"verdict": verdict, "explanation": msg, "order": order},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "confirm":
        confirm_mode()
        return

    print("EPIE001 精簡版 vs 完整版：累積式全新 session 階梯測試")
    print(f"完整版判定門檻：>= {FULL_VERSION_MIN_BYTES:,} bytes 且內容含 'ESSF21.aspx'")
    print(f"已知：精簡版 = 15,275 bytes / 完整版 = 91,694~98,484 bytes")
    print(f"每一階都是全新 session，且只在最後打一次 EPIE001（避免污染 server 狀態）")
    print(f"輸出目錄（已 gitignore）= {OUT_DIR}")

    results = []
    stopped_at = None
    for rung_id, description, init_urls, referer in LADDER:
        r = run_rung(rung_id, description, init_urls, referer)
        results.append(r)
        if r.get("outcome") == "FULL":
            stopped_at = rung_id
            print(f"\n[stop] {rung_id} 已取得完整版 EPIE001 - 依指示停止，不再往下測試、"
                  "也不會去 GET ESSF21。")
            break

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    print(f"\n{'=' * 70}\n總結\n{'=' * 70}")
    print(f"{'Rung':6s} {'Outcome':8s} {'Bytes':>10s}  {'sha256[:12]':14s} {'sid':4s} Referer")
    for r in results:
        e = r.get("epie001")
        if e is None:
            print(f"{r['rung']:6s} {r.get('outcome', '?'):8s} {'-':>10s}  {'-':14s} {'-':4s} -")
            continue
        print(f"{r['rung']:6s} {r['outcome']:8s} {e['body_bytes']:>10,}  {e['sha256_prefix12']:14s} "
              f"{'Y' if e['sessionid_present'] else 'N':4s} {'有' if e['referer_sent'] else '無'}")

    hashes = {r["epie001"]["sha256_prefix12"] for r in results if r.get("epie001")}
    print(f"\n不同的 EPIE001 回應 hash 數量：{len(hashes)}")
    if len(hashes) == 1:
        print("  -> 所有回應「位元組完全相同」，代表這些初始化步驟對 EPIE001 的輸出沒有任何影響，"
              "\n     也代表我們這一連串 GET 並沒有在中途改變 server 狀態（否則回應會有差異）。")

    sid_steps = []
    for r in results:
        for s in r["steps"]:
            if s.get("sessionid_present_after") and not s.get("sessionid_present_before"):
                sid_steps.append((r["rung"], s["short_url"]))
    print(f"\nASP.NET_SessionId 產生於：{sid_steps or '（本次沒觀察到產生時機）'}")

    verdict = {
        "stopped_at_full_version": stopped_at,
        "distinct_epie001_hashes": len(hashes),
        "sessionid_created_at": sid_steps,
        "all_slim": all(r.get("outcome") == "SLIM" for r in results if r.get("epie001")),
    }
    (OUT_DIR / "verdict.json").write_text(
        json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n結果已存到 {OUT_DIR / 'results.json'} / {OUT_DIR / 'verdict.json'}")


if __name__ == "__main__":
    main()
