# Phase 3B：儲存出差人 Browser Ground Truth

**狀態：完成。儲存成功（`hdnGridDataCount` 0 → 1），只按了一次，未送出出差申請單。**

腳本：`scripts/capture_traveler_save.py`（一次性，含防護）
原始資料：`logs/traveler_save_capture/`（已 gitignore）

**最重要的三個發現，都推翻了原本的假設：**

1. **提交機制既不是 A 也不是 B**，而是第三種：一個 0 像素的隱藏 `<input type="image">`
   叫 `BtnDetailSave`，送出的是 `BtnDetailSave.x` / `BtnDetailSave.y` 座標。
   `__EVENTTARGET` 是**空的**，`GridUserControl1$Button9` **完全不在 POST body 裡**。
2. **`CheckPeoplePower` 的 AJAX 會寫入伺服器端 Session**（不只是查詢），所以純 HTTP
   replay 必須先重現它。
3. **點擊前的 DOM 快照無法預測 POST 內容**——onclick 處理鏈會在送出前再改動狀態。

---

## 一、四方 Diff

| 欄位 | 1. Raw HTML | 2. Browser DOM（點擊前） | 3. 實際 POST body | 4. Response 後 |
|---|---|---|---|---|
| `ESSCCDJ023$chk` | 未勾選 | 未勾選、enabled | **不在 body** | 未勾選 |
| `ESSCCDJ023_1$chk` | 未勾選 | 未勾選、enabled | **不在 body** | 未勾選 |
| **`ESSCCDJ038$chk`** | **未勾選** | **已勾選、但 `disabled=True`** | **`on`** | 已勾選 |
| `ESSCCDJ023_hid` | 無 value 屬性 | len=1 | **`'0'`** | len=1 |
| `ESSCCDJ023_1_hid` | 無 value 屬性 | len=1 | **`'0'`** | len=1 |
| `ESSCCDJ038_hid` | 無 value 屬性 | len=1 | **`'1'`** | len=1 |
| `GridUserControl1$hdnBtnSaveEnabled` | `false` | `true`（len 4） | **`false`（len 5）** | `false` |
| `__EVENTTARGET` | 空 | 空 | **空** | 空 |
| `__EVENTARGUMENT` | 空 | 空 | **空** | 空 |
| `__MSPVSTATE` | len 8164 | len 8168, fnv `c9e2e1a3` | len 8168, fnv `c9e2e1a3`（未被 JS 改） | **len 8572, fnv `0befced6`** |
| `__MSPVSTATE_ZIP` | `true` | `true` | `true` | `true` |
| `__VIEWSTATE` | len 0 | len 0 | len 0 | len 0 |
| `GridUserControl1$Button9` | `disabled`, type=submit | **`disabled=False`**（JS 啟用） | **不在 body** | disabled |
| `BtnDetailSave` | type=image, 0px, 有 onclick | **`form.elements` 看不到**（見下） | **`BtnDetailSave.x` + `.y`** | — |
| `DSCScriptManager` | 不是欄位（只是字串） | 不存在 | **存在，len=30** | — |
| `hdnGridData` | 空 | len 0 | 不在 body | **len 217** |
| `hdnGridDataCount` | 空 | len 0 | 不在 body | **len 1 → 已新增一列** |
| `NowGridControlName` | 空 | len 0 | 不在 body | len 16 |

### 每一欄的「陷阱」說明

**`ESSCCDJ038$chk` 三方全都不一樣**，這是整份報告最需要注意的一格：
- raw HTML：沒有 `checked`
- 載入後 JS 把它**勾選並同時設為 disabled** → 因為 disabled，瀏覽器的 `FormData`
  **不會**包含它（這也解釋了為什麼快照 C 的 FormData 只有 117 個而 POST 有 121 個）
- 但實際 POST **有** `ESSCCDJ038$chk=on` → 代表 onclick 處理鏈在送出前把它**重新啟用**了
  （ASP.NET 常見手法，因為 disabled 控制項的值在 postback 會遺失）

**`hdnBtnSaveEnabled` 走了一圈回到原點**：`false`（載入）→ `true`（驗證通過、按鈕啟用）
→ 送出時又變回 **`false`**。onclick 鏈裡的 `SetDetailSaveButtonEnabled()` 會在送出前把
按鈕停用以防重複提交，順手把這個旗標改回 false。**replay 必須送 `false`，不是 `true`。**

**三個 `_hid` 鏡像欄位才是 checkbox 狀態的真正載體**：raw HTML 裡它們連 `value` 屬性都
沒有，但 POST 送的是 `'0'`/`'0'`/`'1'`——跟三個 checkbox 的勾選狀態一一對應。

---

## 二、提交機制的真相

`BtnDetailSave` 在 raw HTML 裡長這樣：

```html
<input type="image" name="BtnDetailSave" id="BtnDetailSave" src=""
       onclick="javascript:WebForm_DoPostBackWithOptions(
                  new WebForm_PostBackOptions('BtnDetailSave', '', true, '', '', false, false))"
       style="width:0px;border-width:0px;" />
```

`WebForm_PostBackOptions` 的最後一個參數是 `clientSubmit=false`，意思是**不要走
`__doPostBack`**，而是讓這個按鈕以原生方式提交表單。原生 `<input type="image">` 提交時
送出的是點擊座標 `name.x` / `name.y`，而**不是** `name=value`——這就是為什麼：

- POST body 有 `BtnDetailSave.x=1`、`BtnDetailSave.y=1`
- `__EVENTTARGET` 是**空的**（沒有走 `__doPostBack`）
- `GridUserControl1$Button9`（你按的那顆）根本不在 body 裡——它只是觸發 JS 的入口，
  真正提交表單的是這顆隱藏的 0 像素按鈕

### ⚠️ 一個會害人踩坑的 DOM 規格細節

快照 C 的具名控制項是 **128** 個，但 raw HTML 解析出 **153** 個，差 **25** 個——正好等於
raw HTML 裡的 25 個 `<input type="image">`。

原因：HTML 規格明確規定 **`form.elements` 排除 `input type="image"`**。

也就是說，**任何只靠瀏覽器 `form.elements` / `FormData` 去推導 payload 的做法，永遠不會
發現 `BtnDetailSave` 的存在**。只有解析原始 HTML 才看得到它。這一點正好證明 Phase 3A
用 raw HTML parser（有抓到 25 個 image input）的方向是對的。

### `DSCScriptManager` 揭露了另一層

POST 回應的 `Content-Type` 是 **`text/plain; charset=utf-8`、31,261 bytes**，不是 HTML。
加上 POST body 裡有一個 raw HTML 中不存在的 `DSCScriptManager`（len=30，由 JS 在送出時
加入）——這代表這次 postback 是 **ASP.NET ScriptManager 的非同步部分回傳
（partial postback / UpdatePanel delta）**，不是整頁重載。

**對 Phase 3C 的意義**：回應不是完整 HTML，不能直接丟給 `parse_form()`。必須先解析
ASP.NET AJAX 的 delta 格式（`長度|類型|id|內容|…` 的管線分隔字串）才能取出新的
`__MSPVSTATE`。

---

## 三、CheckPeoplePower 的 AJAX

輸入出差人代號後 onblur 觸發，**4 筆 POST**（都在 `/HRMESS/` 底下）：

| # | 端點 | body | 性質 |
|---|---|---|---|
| 1 | `ajaxpro/com.digiwin.erpiiplus_app.ess.ESSF21,src.ESS.ESSF21.ashx` | `{"strCode":"<代號>"}` | 查詢 |
| 2 | 同上 | `{"pCode":"<代號>"}` | 查詢（CheckPeoplePower 本體） |
| 3 | `ajaxpro/tw.com.dsc.dscDotNet.kernelBasePage.DSCBasePage,PlatformUtil.ashx` | `{"pUnid":"...","pSessionKey":"MJDscSessionValue","pSessionValue":"<root>…"}` | **寫入 Session** |
| 4 | `src/ESS/ESSF21/ESSF21_MIMJ.aspx` | XML `<root><title>MJ</title><MJCategory>Employee_出差人</MJCategory>…` | 查詢（Content-Type: `text/plain`） |

**第 3 筆是關鍵**：參數名稱直接就是 `pSessionKey` / `pSessionValue`——它把一段 XML
寫進伺服器端的 ASP.NET Session（key 為 `MJDscSessionValue`）。這是明確的
**server-side state 寫入，不是單純查詢**。

驗證完成後，JS 把 12 個明細欄位填好（`ESSCCDD004`～`ESSCCDD015`：代號、姓名、公司/部門/
職位 ID 等，其中幾個是 36 字元的 GUID）。這些值**只能從 AJAX 回應取得**，無法自行推算。

---

## 四、POST 內容總覽

| 項目 | 值 |
|---|---|
| URL | `http://eip.example.com/HRMESS/src/ESS/ESSF21/ESSF21.aspx?...`（form action，含 Identifier） |
| Method | POST |
| Content-Type | `application/x-www-form-urlencoded` |
| body 長度 | 12,816 bytes |
| 欄位數 | **121** |
| Response | 200, `text/plain; charset=utf-8`, **31,261 bytes** |
| Redirect | 無 |
| 對話框 | 無 |

### 121 vs Phase 3A 的 117 欄，差在哪 4 個

| 欄位 | 為什麼 Phase 3A payload 沒有 |
|---|---|
| `BtnDetailSave.x` | image button 座標，只有「點擊」才會產生 |
| `BtnDetailSave.y` | 同上 |
| `DSCScriptManager` | JS 在送出時才加入，raw HTML 裡不存在這個欄位 |
| `ESSCCDJ038$chk` | raw HTML 未勾選；由 JS 勾選，且送出前才被重新啟用 |

反過來「只在 FormData 有、POST 沒有」的欄位：**0 個**。

---

## 五、回答 11 個問題

**1. CheckPeoplePower 是否發生 AJAX？**
是，共 4 筆 POST（見第三節）。其中 `{"pCode":"<代號>"}` 那筆就是 CheckPeoplePower 本體。

**2. AJAX 是否可能建立 server-side state？**
**不是「可能」，是確定會。** 第 3 筆的參數名稱就是 `pSessionKey="MJDscSessionValue"` /
`pSessionValue=<XML>`，明確寫入伺服器端 Session。純 HTTP replay 必須重現它。

**3. Button9 是普通 submit 還是 `__doPostBack`？**
**兩者都不是。** 是第三種機制：0 像素隱藏 image button `BtnDetailSave` 的原生提交，
送出 `BtnDetailSave.x`/`.y`；`__EVENTTARGET` 為空，`GridUserControl1$Button9` 不在 body。
而且整體包在 ScriptManager 的非同步 postback 裡（回應是 `text/plain` delta）。

**4. Browser POST field 共多少？**
**121** 個（body 12,816 bytes）。

**5. 和目前 117-field payload 差哪些？**
多 4 個：`BtnDetailSave.x`、`BtnDetailSave.y`、`DSCScriptManager`、`ESSCCDJ038$chk`。
少 0 個。另外有 3 個欄位**名稱相同但值不同**，這比欄位數差異更危險：
`hdnBtnSaveEnabled` 要送 `false`（不是 DOM 當下的 `true`）、三個 `_hid` 要送 `0/0/1`
（raw HTML 是空的）、以及 12 個 `ESSCCDD004~015` 明細欄位必須先靠 AJAX 取得。

**6. `ESSCCDJ038` checkbox 實際怎麼送？**
送 `ESSCCDJ038$chk=on`，**同時**送 `ESSCCDJ038_hid=1`。兩個機制並用。
raw HTML 兩者都是空的，全靠 JS 補上。

**7. 三個 `_hid` 實際值/狀態如何？**
`ESSCCDJ023_hid='0'`、`ESSCCDJ023_1_hid='0'`、`ESSCCDJ038_hid='1'`，與三個 checkbox 的
勾選狀態一致（未勾=0、已勾=1）。

**8. `hdnBtnSaveEnabled` 何時從 false 改變？**
輸入出差人代號、驗證通過時由 `false` → `true`（同一時刻 Button9 的 `disabled` 由
True → False）。但**送出前又被改回 `false`**，POST 送的是 `false`。

**9. `__MSPVSTATE` 是否在 POST 前被 JS 修改？**
**沒有。** 快照 C 與 POST body 的指紋完全相同（`c9e2e1a3`，長度 8168）→ 原樣回送。

**10. `__MSPVSTATE` 是否在 POST response 後更新？**
**是，而且變化很大。** 8,168 → 8,572 字元（+404），指紋 `c9e2e1a3` → `0befced6`。
後續任何請求**必須使用回應中的新值，禁止重用舊值**。

**11. 是否已具備 Phase 3C HTTP Replay 的條件？**
**尚未完備**，還缺三塊，都不該用猜的：

| 缺口 | 說明 |
|---|---|
| `DSCScriptManager` 的**值** | 只記到長度 30，沒記內容（它不在我的觀察清單裡）。這是 UpdatePanel ID，需要確切字串 |
| POST 的**請求標頭** | ScriptManager 非同步 postback 通常需要 `X-MicrosoftAjax: Delta=true`；本次只記了 Content-Type |
| **delta 回應格式的解析** | 回應是 `text/plain` 31KB 的管線分隔格式，需要寫解析器才能取出新的 `__MSPVSTATE` |

另外 AJAX 那 4 筆的**回應內容**也只記了長度，沒有解析出 12 個明細欄位的對應關係。

---

## 六、儲存結果驗證

依你的要求等 `load` + `networkidle` + 確認 `Form1` 與 `__MSPVSTATE` 都回來才拍快照
（沒有重蹈 `capture_browser_sequence.py` 太早 `.content()` 的錯）。

| 證據 | 結果 |
|---|---|
| `hdnGridDataCount` | 0 → **1**（一筆明細列） |
| `hdnGridData` | 0 → **217 字元** |
| `NowGridControlName` | 0 → 16 |
| `__MSPVSTATE` | +404 字元 |
| 明細輸入欄位 `ESSCCDD004~015` | 全部清空（儲存後重置的正常行為） |
| 對話框 / 錯誤訊息 | 無 |
| POST 回應 | 200 |

**結論：儲存成功。**

補充：畫面上找不到明細清單的 table（`body.innerText` 只有 389 字元），因為表單目前在
`createRecord` 這個 div（單筆輸入模式），清單在另一個隱藏的 div/tab。我沒有為了確認而
去點切換（會改變狀態），改用 `hdnGridDataCount` 這個更可靠的證據。

---

## 七、需要誠實說明的兩件事

### 1. results.json 曾經包含員工編號（已補救）

AjaxPro 把 raw JSON 當成 request body 直接送，我的記錄程式用 `parse_qsl` 解析後，整段
JSON 被當成「欄位名稱」記了下來——結果員工編號進到了本該只有名稱的紀錄裡，違反我
自己宣告的遮罩規則。

已處理：把 56 處出現全部替換為 `<EMPCODE_MASKED_len6>`，JSON 結構完整保留、仍可解析。
（`logs/` 本來就在 .gitignore 內，且同一組編號早已出現在 `docs/eip-analysis.md` 的
frame URL 裡，所以實際外流風險為零，但規則就是規則。）

未來若要記錄 AjaxPro 這種 raw-JSON body，必須先判斷 Content-Type 不是真正的
form-encoded，不能無條件套 `parse_qsl`。

### 2. 表頭填了測試資料

為避免唯一一次點擊被 `saveCheckD` / `CheckDetailForm` 驗證擋掉，事先填入了明顯的假資料
（`2026/01/01`、`測試地點`、`測試事由`）。這只存在於草稿，沒有送出。純淨快照 A 是在
填表頭**之前**拍的，所以「raw HTML vs JS 執行後 DOM」的比較沒有被污染。

### 3.（附帶）長期登入問題找到解法了

這次啟動 debug Edge 時加上 `--auth-server-allowlist=*.example.com`，**SSO 直接自動
完成，不需要任何手動介入**。

這推翻了 `docs/login-automation-investigation.md` 的部分結論：那份文件把反覆出現的
`chrome-error://chromewebdata/` 判斷為「Chromium 內部 NTLM 協商不穩定」，但真正的原因
是這個獨立 profile 沒有套用自動 SSO 白名單，Edge 其實一直在跳 Windows 認證對話框，
沒人回應才變成錯誤頁。當初測過這個參數「無效」，是因為那次測的是另一個問題
（Playwright `page.goto()` 導覽被擋，與白名單無關）。

---

## 八、目前狀態

- 儲存出差人**只執行一次**，`logs/traveler_save_capture/ALREADY_EXECUTED.marker` 已建立，
  重跑會被拒絕
- 未送出出差申請單、未按 `MasterPage_btnCreateToolSendForm`、未呼叫 `btClosejQTab`
- 未執行任何 `requests.post()` / HTTP replay
- 未修改正式 Playwright/CDP 流程（`src/` 內舊檔案時間戳皆未變動）
- **未進入 Phase 3C**，等待你確認
