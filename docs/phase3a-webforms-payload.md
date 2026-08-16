# Phase 3A：WebForms State Parser + POST Payload Builder

**狀態：完成，全程零 POST。**

純 HTTP 路線現在可以：穩定取得 144KB 的真實 ESSF21 表單 → 完整解析 153 個控制項
（含全部 63 個 hidden 欄位）→ 在記憶體中建立正確的 POST payload。**沒有送出任何東西。**

新增檔案（都不影響現有 Playwright/CDP 路線，該路線檔案完全未修改）：

| 檔案 | 內容 |
|---|---|
| `src/webforms_state.py` | `parse_form(html)` → `FormState`；依 HTML successful controls 規則產生送出清單。純 stdlib，不相依 playwright/requests |
| `src/http_eip_client.py` | `HttpEipClient`：`authenticate()` / `initialize_efnet()` / `open_trip_wrapper()` / `open_trip_form()` |
| `src/http_trip_form.py` | `build_trip_payload(form_state, trip_request)`，只在記憶體修改 |
| `scripts/http_trip_payload_dry_run.py` | 實際 GET → 解析 → 建 payload → 印遮罩過的 diff |
| `tests/test_webforms_state.py` | 14 個測試 |
| `tests/test_http_trip_form.py` | 12 個測試 |

測試：**66 passed**（原本 40，新增 26）。

## POST 防護是程式強制的，不是靠約定

`HttpEipClient` 預設用 `_GetOnlySession`，它把 `post` / `put` / `patch` / `delete`
全部覆寫成直接丟 `ReadOnlyViolation`。要進入會改變伺服器狀態的階段，必須明確寫
`HttpEipClient(read_only=False)`——不可能因為手滑而發生。

---

## 一、驗證數據（實際執行 `http_trip_payload_dry_run.py`）

```
ASP.NET_SessionId 取得：是
EPIE001：97,070 bytes（完整版）
ESSF21 ：144,500 bytes
form    ：name="Form1" method="post"
```

### Parser 結果與一致性檢查

| 項目 | Parser | 原始 HTML regex | |
|---|---|---|---|
| input 總數 | 149 | 149 | OK |
| textarea | 4 | 4 | OK |
| select | 0 | 0 | OK |
| **hidden** | **63** | **63** | **OK** |
| text | 49 | 49 | OK |
| checkbox | 3 | 3 | OK |
| radio | 2 | 2 | OK |
| submit | 7 | 7 | OK |
| image | 25 | 25 | OK |

`total_controls = 153`（149 input + 4 textarea），`disabled = 12`，`unnamed = 0`，
**`successful_controls = 117`**。

117 這個數字可以對帳：153 − 25 image − 7 submit = 121；再扣掉 3 個未勾選的 checkbox
和 1 個未選中的 radio = 117。12 個 disabled 全部都是按鈕，本來就已被類型規則排除。

原始 HTML 的 `<script>` 內含 0 個 input，parser 仍會略過 script 內容，避免未來頁面改版
時 JS 字串裡的標籤被誤認為控制項。

---

## 二、關鍵發現（都會影響未來的 POST 正確性）

### 1. `__VIEWSTATE` 是空的 — 真正的狀態在 `__MSPVSTATE`

| 欄位 | 存在 | 長度 |
|---|---|---|
| `__VIEWSTATE` | ✅ | **0** |
| `__VIEWSTATEGENERATOR` | ❌ 不存在 | — |
| `__EVENTVALIDATION` | ❌ 不存在 | — |
| **`__MSPVSTATE`** | ✅ | **8,164** |
| `__MSPVSTATE_ZIP` | ✅ | 4（值是 `true`，代表有壓縮） |
| `__TabStrip2_State__` | ✅ | 1 |

這套系統用自己的 `__MSPVSTATE`（壓縮過）取代了標準 ViewState。任何未來的 postback
**必須原樣回送 `__MSPVSTATE`，而且絕對不要嘗試自行產生或修改它**——它是壓縮後的
不透明資料。只盯著 `__VIEWSTATE` 會完全抓錯重點。

### 2. 三個欄位是 `<textarea>` 不是 `<input>`

| 欄位 | 標籤 |
|---|---|
| `ESSCCDJ024/025/026/027`（日期時間） | `<input type="text">` |
| **`ESSCCDJ028`（出差地點）** | **`<textarea>`** |
| **`ESSCCDJ037`（出差原因）** | **`<textarea>`** |
| **`ESSCCDJ029`（備註）** | **`<textarea>`** |
| `ESSCCDD005`（出差人代號） | `<input type="text">` |

textarea 的值是**標籤之間的文字內容**，不是 `value` 屬性。如果 parser 只讀 `value`，
這三個欄位會靜默地變成空字串——表單看起來有送出，但地點、事由、備註全空。

### 3. ⚠️ 原始 HTML 的 checkbox 狀態與瀏覽器 DOM **不一致**

`docs/eip-analysis.md` 第 8 節記錄（透過 Playwright 觀察 DOM）：那三個 checkbox
「目前預設只勾選第 3 個」。

但**原始 HTML 裡三個都沒有 `checked`**：

```
checkbox ESSCCDJ023$chk     checked=False
checkbox ESSCCDJ023_1$chk   checked=False
checkbox ESSCCDJ038$chk     checked=False   ← 瀏覽器 DOM 裡這個是勾的
```

也就是說 **`ESSCCDJ038_chk` 是頁面載入後由 JavaScript 勾選的**。

**這是目前純 HTTP 路線最大的正確性風險**：直接用原始 HTML 建 payload，送出的 checkbox
狀態會跟真人操作不同（少送 `ESSCCDJ038$chk=on`），可能導致工時計算結果不一樣。
另外這三個 checkbox 都有對應的 hidden 鏡像欄位（`ESSCCDJ023_hid` / `ESSCCDJ023_1_hid` /
`ESSCCDJ038_hid`，目前都沒有 value 屬性），真正的狀態可能是靠這些 hidden 欄位傳遞的。

**這件事必須在任何 POST 之前先釐清**，而且答案要從觀察真實瀏覽器送出的內容取得，
不能用猜的。已列入下方 capture plan。

### 4. 儲存出差人的按鈕目前是 `disabled`

```html
<input type="submit" name="GridUserControl1$Button9" value="儲存"
       id="GridUserControl1_Button9" disabled="disabled" class="newbutton"
       onclick="if(!saveCheckD('createRecord')){...}
                if (!CheckDetailForm('createRecord')) {...}
                if(!SetDetailSaveButtonEnabled(this, checkRequiredFields_GridUserControl1())){...}" />

<input name="GridUserControl1$hdnBtnSaveEnabled" type="hidden"
       id="GridUserControl1_hdnBtnSaveEnabled" value="false" />
```

按鈕在剛載入時是停用的，由 JS 驗證通過後才啟用，並且有一個 `hdnBtnSaveEnabled`
hidden 欄位目前是 `"false"`。依你的指示，**這裡沒有猜測它按下後需要哪些 state**，
payload builder 也刻意完全不加入任何按鈕欄位。

### 5. id 與 name 的處理方式

沒有做 `_` → `$` 的字串轉換，而是**用 id 在解析結果裡查出 HTML 實際宣告的 name**：

| logical | DOM id | 實際 POST name |
|---|---|---|
| start_date | `ESSCCDJ024_txt` | `ESSCCDJ024$txt` |
| location | `ESSCCDJ028_txt` | `ESSCCDJ028$txt` |
| … | … | … |

字串轉換在這個頁面上「剛好」會對，但不能依賴：`ESSCCDJ023_1_chk` 的 name 是
`ESSCCDJ023_1$chk`（只換最後一個底線），若日後出現 ASP.NET naming container 前綴
（`ctl00$...`）就會整個錯掉。已有測試覆蓋這個情境。

---

## 三、Payload Dry Run 結果（遮罩後）

```
method=post   欄位總數=117   不重複 name=117

修改的 7 個欄位：
  ESSCCDJ024$txt  tag=<input>     old_length=0  new_length=10
  ESSCCDJ025$txt  tag=<input>     old_length=0  new_length=5
  ESSCCDJ026$txt  tag=<input>     old_length=0  new_length=10
  ESSCCDJ027$txt  tag=<input>     old_length=0  new_length=5
  ESSCCDJ028$txt  tag=<textarea>  old_length=0  new_length=8
  ESSCCDJ037$txt  tag=<textarea>  old_length=0  new_length=4
  ESSCCDJ029$txt  tag=<textarea>  old_length=0  new_length=14

保留的 state：
  __VIEWSTATE       preserved=True  length=0
  __MSPVSTATE       preserved=True  length=8,164
  __MSPVSTATE_ZIP   preserved=True  length=4
  __TabStrip2_State__ preserved=True length=1

未修改而原樣保留：110 個（63 個 hidden 全部保留）
GridUserControl1$Button9：不在 payload 中 ✅
```

Dry run 使用明顯的假資料（`2026/01/01` / `測試地點測試地點` 等），不涉及任何真實出差資訊。

---

## 四、Phase 3B Capture Plan（本輪只提出，未執行）

目標：觀察真人按下「儲存出差人」（`GridUserControl1_Button9`）時，瀏覽器實際送出的
HTTP 請求，以便重建而非猜測。

### ⚠️ 必須先取得你的同意的原因

捕捉這個請求**必然要在真實瀏覽器上實際執行一次「儲存出差人」**——這是會改變伺服器
狀態的動作（會在草稿單上新增一列出差人明細）。它**不等於送出出差申請單**（那是另一個
「傳送」按鈕），但仍然不是唯讀操作。本輪依指示沒有觸發，也不會自行觸發。

### 需要捕捉的內容

| # | 項目 | 為什麼需要 |
|---|---|---|
| 1 | POST URL（完整，Identifier 遮罩） | 確認是打回 `ESSF21.aspx?...` 自己（form action）還是別的端點 |
| 2 | **提交機制判定**：是 `GridUserControl1$Button9=儲存` 這個欄位，還是 `__doPostBack` 設定 `__EVENTTARGET` | 這是最關鍵的分歧點。按鈕是 `type="submit"`，理論上會以欄位形式送出；但 onclick 鏈最後可能改呼叫 `__doPostBack`。兩者建 payload 的方式完全不同，不能猜 |
| 3 | `__EVENTTARGET` 的值 | 若走 postback 路線，需要知道確切的 target 字串 |
| 4 | `__EVENTARGUMENT` 的值 | 同上 |
| 5 | 完整 POST field names 清單 | 與我們 payload 的 117 個 name 做差集比對，找出缺漏或多餘 |
| 6 | `GridUserControl1$hdnBtnSaveEnabled` 送出時的值 | 目前 HTML 是 `"false"`，JS 應該會改成 `"true"`；需確認送出的是什麼 |
| 7 | **三個 checkbox 送出時的實際狀態** | 直接解決上面第 2.3 節的落差：真人送出時 `ESSCCDJ038$chk` 到底有沒有出現在 body 裡 |
| 8 | 三個 `_hid` 鏡像欄位送出時的值 | 判斷 checkbox 狀態是靠 checkbox 本身還是 hidden 欄位傳遞 |
| 9 | `__MSPVSTATE` 送出時的長度（值不記錄） | 確認是原樣回送，還是 JS 會在送出前改寫 |
| 10 | 送出前是否有 AjaxPro XHR | `ESSCCDD005_txt` 的 onblur 會呼叫 `CheckPeoplePower(pCode)`，先前的 browser capture 也看到 `ajaxpro/*.ashx`。若這個 AJAX 會在伺服器端建立狀態，純 HTTP 就必須先重現它 |
| 11 | response status | |
| 12 | redirect chain | 有無 302，導向何處 |
| 13 | response body 長度與是否含錯誤訊息 | |
| 14 | **回應中新的 hidden state**（`__MSPVSTATE` 新長度 + hash 前 8 碼） | 確認 postback 後 state 有更新，後續步驟必須改用新的，不能重用舊的 |

### 建議做法

新增獨立的被動觀察腳本（例如 `scripts/capture_traveler_save.py`），**不要修改**
`src/network_log.py` 或 `src/trip_form.py`。現有的 `NetworkRecorder` 只記錄欄位名稱、
不記錄值，且沒有記錄 request headers 與回應中的新 state，資訊量不足以完成上表。

遮罩規則沿用既有標準：`__MSPVSTATE` / `__VIEWSTATE` / Identifier / Cookie /
Authorization / 個資一律只記長度或 hash 前 8 碼。

### 順帶修掉的既有技術債

`scripts/capture_browser_sequence.py` 目前在 frame 網址一出現就讀取 `.content()`，
沒有等 `load`/`networkidle`，會抓到渲染中的殘缺 HTML（先前存到 1,409 bytes 而非真實的
144,494）。新的捕捉腳本不應重蹈覆轍。

---

## 五、目前狀態

- Phase 3A 完成，66 個測試全過
- 本輪**零 POST**：新增的 4 個檔案裡沒有任何 `.post(` 呼叫，且 client 在程式層強制唯讀
- 未修改任何 Playwright/CDP 路線檔案
- 未觸發儲存出差人、未暫存草稿、未傳送、未呼叫 `btClosejQTab`
- **未進入 Phase 3B**，等待你的指示
