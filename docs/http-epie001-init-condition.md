# EPIE001 精簡版 / 完整版的真正切換條件

**結論**：切換條件是**在同一個 session 裡有沒有 GET 過 `CollectData.aspx`**。
有走 → 完整版（約 91.7 KB，含 `framePlus`／`ESSF21.aspx`／`Identifier`／`hdnplusFrameUrl`）；
沒走 → 精簡版（15,275 bytes，四個標記全無）。

**Referer 已可排除**，`platform.aspx` 也不是必要步驟——成功的那一組（S2）兩者都沒有。

腳本：`scripts/http_epie001_init_ab_test.py`（純 GET，未修改 `src/` 任何檔案）
原始資料：`logs/http_epie001_init_ab_test/`（已 gitignore）

---

## 網址來源（不猜測，但要說清楚出處）

必須先誠實講一件事：`logs/browser_capture/sequence.json` **並不包含**點擊前的 frameset
載入序列——那次錄製是在點擊前才 attach，當時外框早就載入完了，所以 capture 裡的第一筆
就已經是 EPIE001 本身。因此初始化網址不可能從 capture 推導，實際來源是：

| 資料 | 來源 |
|---|---|
| Referer 值 `…/FrameSet/platform.aspx` | `logs/browser_capture/sequence.json` seq=1，真實捕捉到的瀏覽器實際送出值 |
| 各初始化 ASPX 網址 | `docs/eip-analysis.md` 第 1 節的真實 frame 表（真實登入 session 觀察） |
| **`CollectData.aspx`** | `logs/http_explorer/findings.json` step2——`/EFNET/` 首頁的 frame src 其實是 `CollectData.aspx`，它會轉往 `TreeMainFrame.aspx` |

`CollectData.aspx` 這一條是這次的關鍵線索，之前一直被忽略：先前所有失敗的探測都是
**直接打 `TreeMainFrame.aspx`**，跳過了 `CollectData.aspx`。

---

## 測試設計

依你的要求採 cumulative fresh-session：每一階都是**全新 `requests.Session()`**、
自己重新 SSPI 驗證、且**只在最後打一次 EPIE001**，絕不在同一 session 內重複打
EPIE001（因為 GET EPIE001 本身可能改變伺服器狀態）。

## 第一輪：升序階梯

| Rung | 初始化序列 | EPIE001 結果 | Bytes | sha256[:12] | 耗時 |
|---|---|---|---|---|---|
| S0 | 首頁 | **SLIM** | 15,275 | `cc52546a88ab` | 765ms |
| S1 | 首頁 → TreeMainFrame（直接，跳過 CollectData） | **SLIM** | 15,275 | `cc52546a88ab` | 203ms |
| S2 | 首頁 → **CollectData**（自動轉 TreeMainFrame） | **FULL** ✅ | 91,702 | `e614ad664fd3` | 3,687ms |

S2 成功後依指示立即停止，S3～S7（含 browser-like 完整初始化、含 Referer 那兩組）**都沒有執行**——
因為已經不需要了：最小的成功組合只需要「首頁 + CollectData」兩步。

## 中途插曲：暫時性阻塞（如實記錄）

第一次交錯確認時，S2 連續 **3 次讀取逾時**（20 秒上限），而 S0/S1 依舊秒回精簡版。
因為第一次成功只花 3,687ms，20 秒不是「剛好差一點」，所以我做了**一次**有上限的探測
（單一 GET、90 秒上限）來區分「變慢」還是「被卡住」——結果 **0.4 秒就回了完整版
91,698 bytes**。

所以那 3 次是**暫時性阻塞，不是系統性失敗**。這也讓我把量測工具的 timeout 從 20 秒
調到 60 秒（寫在程式註解裡說明理由）——因為精簡版永遠是「秒回且位元組完全相同」，
把「暫時卡住」誤判成「伺服器刻意回精簡版」會導出完全錯誤的結論。

**這個暫時性阻塞本身還沒有解釋**，是目前唯一還懸著的異常現象（見下方第 6 題）。

## 第二輪：交錯確認（刻意從 S2 開始，排除時間點因素）

| # | Rung | 有走 CollectData | 結果 | Bytes | sha256[:12] |
|---|---|---|---|---|---|
| 1 | S2 | ✅ | **FULL** | 91,698 | `de2a4df35eaa` |
| 2 | S0 | ❌ | SLIM | 15,275 | `cc52546a88ab` |
| 3 | S2 | ✅ | **FULL** | 91,698 | `026e05609f95` |
| 4 | S1 | ❌ | SLIM | 15,275 | `cc52546a88ab` |
| 5 | S2 | ✅ | **FULL** | 91,698 | `28e4e4d8f993` |

**判定：`CONFIRMED_COLLECTDATA_IS_THE_TRIGGER`**

兩個細節讓這個結論特別有力：

1. **S0/S1 的 hash 每次都完全相同**（`cc52546a88ab`）——精簡版是同一份、位元組級一致的
   回應，不是「有時多有時少」的隨機結果。
2. **S2 的 3 次 hash 全都不同**（長度都是 91,698，但內容不同）——因為每次都含一個
   **全新的 Identifier**。這正是預期行為，也順便證明每次 GET 都真的產生了新的 Identifier。

累計統計：**S2 在伺服器有回應時 5/5 全部完整版**（升序那次 + 90 秒探測 + 交錯 3 次），
**S0/S1 共 4/4 全部精簡版**。順序刻意打亂後模式不變，時間點因素已排除。

---

## 回答你的 6 個問題

**1. 哪一個 initialization step 讓 EPIE001 從精簡版變完整版？**
**`CollectData.aspx`**，而且只需要這一步。最小成功組合是「GET `/EFNET/` → GET
`CollectData.aspx` → GET `EPIE001.aspx?FormID=ESSF21`」共三個請求。不需要 tree、
Marquee、ShowStatus、titlebar1、platform、main、HomeTab 任何一個。

**2. ASP.NET_SessionId 在哪一步產生？**
**由該 session 的第一個 ASPX 請求產生，沒有特定歸屬**——實測三種情況：S0 由 EPIE001
自己產生、S1 由 TreeMainFrame 產生、S2 由 CollectData 產生。（`/EFNET/` 首頁本身是
靜態 HTML、不會產生。）

**關鍵推論：SessionId 的存在與否不是切換條件。** S1 明明已經有 SessionId，EPIE001 還是
給精簡版。所以真正被 `CollectData.aspx` 建立的是**某種 session 內的應用層狀態**，
不只是「有一個 session」而已。

**3. platform.aspx 是否為必要步驟？**
**不是。** S2 完全沒有碰 `platform.aspx`，5/5 都拿到完整版。

**4. Referer=platform.aspx 是否可能是必要條件？**
**不是，可以排除。** S2 的 EPIE001 請求**沒有帶任何 Referer**，5/5 都拿到完整版。
你原本設計的 Experiment 4（拆分「初始化序列」vs「Referer」）答案已經明確落在
**A：初始化 GET sequence**——而且不需要額外實驗，因為 S2 本身就是「有初始化、無 Referer」
的乾淨對照組。上一輪 `docs/http-essf21-referer-ab-test.md` 判定 INCONCLUSIVE 的原因也
同時解釋了：那 6 個 session 全都直接打 EPIE001，沒有一個走過 CollectData。

**5. Browser initialization 是否已能由 requests 重現？**
**在 EPIE001 這一層：可以，而且穩定重現（5/5）。** 而且比原本猜測的簡單得多——不需要
重播整個 frameset，只要多一個 `CollectData.aspx` 請求。

至於 ESSF21 那一層還不知道，因為依你的指示這次**沒有去 GET ESSF21**。

**6.「user-level single tab lock」假設是否還有必要保留？**
**作為「精簡版/完整版」的解釋：不需要了，已被取代。** 那個現象完全由「有沒有走
CollectData」解釋，跟跨 session 的使用者層鎖無關——證據是同一時間窗內交錯執行，
S2 一直成功、S0/S1 一直失敗。

**但不要完全丟掉**：那 3 次連續逾時是真實發生的、目前仍未解釋的現象。它的形態（阻塞
而非回精簡版）跟原本設想的鎖不一樣，但確實像某種伺服器端的短暫競爭/鎖定。而且它**可能
跟先前 ESSF21 回應空 body（Content-Length 0）是同一個根因**——兩者都是「該有內容卻
沒有」，而且都出現在剛剛才成功過一次之後。這條線值得保留觀察，但目前沒有證據，不當結論。

---

## 這次順帶釐清的歷史疑點

之前所有「成功一次就再也不重現」的紀錄，現在全部對上了：

| 事件 | 有走 CollectData？ | 結果 |
|---|---|---|
| `http_eip_explorer.py` 第一次執行 | ✅ 有（Step 2 爬 frame 時，`/EFNET/` 的 frame src 就是 CollectData） | 成功拿到完整版 + 真正的 ESSF21 網址 |
| `followup_probe.py`（直接打 TreeMainFrame） | ❌ 跳過 | 失敗 |
| `followup_probe2.py`（直接打 EPIE001 ×4） | ❌ 跳過 | 4 次全失敗 |
| Referer A/B Test（6 個 session 直接打 EPIE001） | ❌ 全部跳過 | 6 次全精簡版 |
| 真實瀏覽器點擊 | ✅ 有（瀏覽器載入 frameset 時必然會走） | 成功 |

**完全一致，沒有例外。** 不是「時運」，是一個一直存在但沒被發現的必要步驟。

---

## 目前狀態

依你的停止條件：已取得完整版 EPIE001，**沒有去 GET ESSF21**、沒有任何 POST、
沒有呼叫 `btClosejQTab`、沒有修改正式 Playwright 流程、沒有進 Phase 3。

下一步如果要繼續，最自然的最小實驗是：**在同一個「走過 CollectData」的 session 裡，
拿到 fresh Identifier 後立刻 GET 一次 ESSF21**，看看先前那個 Content-Length 0 是不是
也同樣源自缺少 CollectData 初始化。這需要你的同意（會實際 GET ESSF21），這次不會自行執行。
