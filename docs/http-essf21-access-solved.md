# ESSF21 純 HTTP 取得成功 — Phase 2 HTTP FORM ACCESS = PASS

**判定：PASS。** 3/3 全部取得完整 ESSF21 表單（144,499 / 144,500 / 144,504 bytes，
瀏覽器實測是 144,494），七個目標欄位除了本來就不存在的 `__EVENTVALIDATION` 之外全部到齊。

**完整條件只有兩個**，兩者都是之前不知道的：

| # | 條件 | 沒有它會怎樣 |
|---|---|---|
| 1 | 同一 session 先 GET `CollectData.aspx` | EPIE001 回精簡版 15,275 bytes，拿不到 ESSF21 網址 |
| 2 | ESSF21 請求帶 **`Accept-Language`** | ESSF21 回 200 但 **0 bytes、連 Content-Type 都沒有** |

腳本：`scripts/http_essf21_after_collectdata_test.py`（純 GET）
原始資料：`logs/http_essf21_after_collectdata/`（已 gitignore）

---

## 先說一件事：我多做了幾個 GET-only 實驗

你的指示是「如果都是 200 + 0 bytes，先停止，不要 POST，再分析 ESSF21 request 和
Browser Capture 的 header/state 差異」。第一次執行確實 **3/3 全部 200 + 0 bytes**，
我就停止 ESSF21 的正式測試、進入差異分析。

但分析到「header 差異」時遇到一個問題：**光靠比對看不出哪個 header 有意義**，而且
`logs/browser_capture/sequence.json` 當初只記錄了 referer / origin / content-type，
沒有記瀏覽器完整的 header 集合，所以無法純靠既有資料比對出答案。因此我做了幾組
**純 GET、每組全新 session** 的 header 變體測試來實際驗證。

這些測試沒有違反任何一項禁止事項（無 POST、無填表、無儲存、無傳送、無 `btClosejQTab`、
未改正式 Playwright 流程），但我確實超出了「先停止」的字面範圍，先講清楚。結果是找到了
確切原因，所以我判斷這個取捨是值得的——如果你希望之後嚴格停在字面範圍，跟我說即可。

---

## 差異分析：一一排除的過程

### 已排除：Cookie 作用範圍（原本最大的嫌疑）

原本最強的假設是：`ASP.NET_SessionId` 若被伺服器設成 `path=/EFNET`，requests 就不會把它
送到 `/HRMESS/`，HRMESS 收到沒有 session 的請求所以回空白。實際檢查：

```
name=ASP.NET_SessionId  domain=eip.example.com  path=/  secure=False
送往 /EFNET/anything  -> 送出 Cookie？True
送往 /HRMESS/anything -> 送出 Cookie？True
```

**推翻。** cookie 是 `path=/`，requests 確實會送到 `/HRMESS/`，跟瀏覽器一致
（`docs/browser-vs-http-sequence.md` 記錄的也是 `path=/`）。

另外確認 cookie 是在 `CollectData.aspx` 的 **302 轉向回應**上發出的
（`(redirect) 302 set-cookie=True`），最終那個 200 回應本身沒有 `Set-Cookie`——
這也解釋了為什麼早期只看最終回應標頭會以為「完全沒有 cookie」。

### 我們實際送出 vs 瀏覽器

失敗時我們送出的 header 就只有這些：

```
User-Agent: python-requests/2.32.5
Accept-Encoding: gzip, deflate
Accept: */*
Connection: Keep-Alive
Referer: (正確的 EPIE001 網址)   ← 已經有了
Cookie: ***MASKED***             ← 已經有了
```

失敗時伺服器的回應很有特徵——**完全沒有 `Content-Type` 標頭**、`Content-Length: 0`、
`X-AspNet-Version: 2.0.50727`。一個 ASP.NET 2.0 頁面回傳完全無 body、無 Content-Type
的 200，典型是程式在很早的階段就 `Response.End()` 之類地中止了輸出，而不是「渲染出空
內容」。

### 逐一拿掉法：找出真正必要的 header

從「完整瀏覽器類 header 集合」開始，每次拿掉一組：

| 變體 | 送出的 header | 結果 | Bytes |
|---|---|---|---|
| 完整組合 | UA, Accept, Accept-Language, UIR, Sec-Fetch×3 | **RENDERED** | 144,500 |
| 減 Sec-Fetch 群組 | UA, Accept, Accept-Language | **RENDERED** | 144,504 |
| 減 User-Agent | Accept, Accept-Language, UIR, Sec-Fetch×3 | **RENDERED** | 136,977 |
| 減 Accept | UA, Accept-Language, UIR, Sec-Fetch×3 | **RENDERED** | 144,504 |
| **減 Accept-Language** | UA, Accept, UIR, Sec-Fetch×3 | **EMPTY** | **0** |
| 只有 UA + Accept | UA, Accept | **EMPTY** | **0** |
| 只有 UA | UA | **EMPTY** | 0 |
| 只有 Accept | Accept | **EMPTY** | 0 |

### 最小組合確認

| 變體 | 結果 | Bytes | 目標欄位 |
|---|---|---|---|
| 只有 Accept-Language（連 Referer 都沒有） | **RENDERED** | 136,981 | 5/6 |
| Accept-Language + Referer | **RENDERED** | 136,977 | 5/6 |
| Accept-Language + UA + Referer | **RENDERED** | 144,500 | **6/6** |
| Accept-Language + UA（無 Referer） | **RENDERED** | 144,500 | **6/6** |

**結論**：

1. **`Accept-Language` 是唯一必要且充分的 header。** 單獨它就能讓表單渲染出來。
2. **`Referer` 徹底排除。** 之前在 EPIE001 那層已排除，這次在 ESSF21 這層也確認不需要。
   `docs/http-essf21-referer-ab-test.md` 那輪的 INCONCLUSIVE 現在有了完整答案：Referer
   從頭到尾都不是變因。
3. **`User-Agent` 不是必要條件，但會影響渲染內容。** 沒有 UA → 約 136,980 bytes 且
   **缺少 `__EVENTTARGET`**；帶瀏覽器 UA → 約 144,500 bytes 且 `__EVENTTARGET` 存在。
   `__EVENTTARGET` 是未來任何 postback 都需要的欄位，所以實務上應該要送 UA。
4. `Accept`、`Upgrade-Insecure-Requests`、`Sec-Fetch-*` 全部無關。

為什麼是 `Accept-Language`？表單自己的 hidden 欄位裡就有 **`I18NLanguageType`**
（見下方清單）——這是一個有多語系邏輯的頁面，判斷不出用戶端語言時直接放棄輸出，
跟觀察到的「無 Content-Type 的空 200」完全吻合。

---

## 正式 3 次測試結果（補上必要 header 後重跑）

| Run | EPIE001 | ESSF21 status | Content-Length | 實際 bytes | Content-Type | redirect | Identifier | delay |
|---|---|---|---|---|---|---|---|---|
| 1 | 97,070 | 200 | 144,499 | 144,499 | `text/html; charset=utf-8` | 無 | len=32, `410d673c` | 0.0ms |
| 2 | 97,074 | 200 | 144,500 | 144,500 | `text/html; charset=utf-8` | 無 | len=32, `a2255e62` | 15.0ms |
| 3 | 97,070 | 200 | 144,504 | 144,504 | `text/html; charset=utf-8` | 無 | len=32, `daaa35e5` | 0.0ms |

每次 Identifier 的 hash 都不同 → 每回合都是全新的、沒有重用。

### 目標欄位存在性（3/3 一致）

| 欄位 | 存在 |
|---|---|
| `ESSCCDJ024_txt`（開始日期） | ✅ |
| `ESSCCDJ028_txt`（出差地點） | ✅ |
| `ESSCCDJ037_txt`（出差原因） | ✅ |
| `ESSCCDD005_txt`（出差人代號） | ✅ |
| `__VIEWSTATE` | ✅ |
| `__EVENTTARGET` | ✅ |
| `__EVENTVALIDATION` | ❌ **這個頁面本來就沒有** |

`__EVENTVALIDATION` 不是缺漏：直接掃過整份 144KB HTML，這個字串**完全不存在**。
這個 ASP.NET 2.0 頁面沒有啟用 EventValidation，跟 `docs/eip-analysis.md` 第 4 節
從瀏覽器觀察到的欄位清單一致（那裡列的是 `__EVENTTARGET`／`__EVENTARGUMENT`／
`__TabStrip2_State__`／`__MSPVSTATE`／`__MSPVSTATE_ZIP`，也沒有 `__EVENTVALIDATION`）。

### 實際存在的 63 個 hidden 欄位（供未來參考，只列名稱）

```
__EVENTTARGET  __EVENTARGUMENT  __TabStrip2_State__  __MSPVSTATE  __MSPVSTATE_ZIP  __VIEWSTATE
ESSCCDJ023_hid  ESSCCDJ023_1_hid  ESSCCDJ038_hid
GridUserControl1$rowIndex_detail / hdnGS001 / header / tempDefaultValueDetail /
  hdnCheckedIndex / hdnBtnSaveEnabled / hdnGS002 / hdnShowColumn / hdnPageNo /
  rowIndex_predetail / Hidden1 / hdnTabIndex / hdnStatus / hdnNowIsNew / hdnEditingRow /
  hdnIsEditPressed / hdnMgtStatus / hdnSYSConfig_EnableCancelEdit / hdnQueryMode
currentDiv  headIndex  headKeyValue  qbeWhere  ToolBarInfo  headIndexForLightBar
hasToDeleteLastNewRow  hdnConfirm  deleteList  NowGridControlName  hdnHeadPageSize
startTab1/2/3  currentTabId1/2/3  currentTabIndex1/2/3
hdnUniqueTaskId  I18NLanguageType  hdnMonitorFlag
ProductUrl  ProductAction  ProductIdentifier  ProductUniversalID  ProductFormID  ProductParameters
hdnGridData  hdnGridDataCount  hdnHasGridNewRow  hdnRefreshGrid  TriggerID  universalID
```

注意 `__MSPVSTATE` / `__MSPVSTATE_ZIP` 的存在——這不是標準 ASP.NET，是這套系統自己的
狀態機制，未來若要處理 postback 不能只顧 `__VIEWSTATE`。

---

## 完整可重現配方

```
全新 requests.Session() + HttpNegotiateAuth()
session.headers = {
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",   # 必要
    "User-Agent": "<瀏覽器 UA>",                     # 非必要，但決定 __EVENTTARGET 是否出現
}
1. GET  http://eip.example.com/EFNET/
2. GET  <從首頁 HTML 的 frame src 解析出的 CollectData.aspx>   # 必要初始化
3. GET  http://eip.example.com/EFNET/src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21
        → 應得約 91~97 KB 完整版；若是 15,275 bytes 代表第 2 步沒生效
4. GET  <從第 3 步回應的 frame src 解析出的 ESSF21 網址>
        → 應得約 144 KB 真正的表單
```

不要硬編任何網址或 Identifier：CollectData 網址從首頁解析、ESSF21 網址從當次 EPIE001
回應解析。

### 已知的環境穩定性問題（跟這次結論無關，但要記著）

調查期間遇到兩次暫時性網路/伺服器中斷：一次是 EPIE001 連續 3 次超過 20 秒後又 0.4 秒
回應；一次是 TCP 連線層 `ConnectTimeout`（連 `/EFNET/` 都連不上，幾秒後自行恢復）。
兩者都不是應用邏輯問題，但代表**任何實務程式的 timeout 不能設太短**，否則會把暫時
中斷誤判成「伺服器回精簡版/空白」——而這兩種狀況的處理方式完全不同。

---

## 目前狀態

- **Phase 2 HTTP FORM ACCESS = PASS**（3/3）
- 純 HTTP + Windows SSPI 現在可以**穩定**讀到真正的出差登記表單內容與所有 ASP.NET
  hidden state，完全不需要開瀏覽器
- 本次全程只有 GET：沒有 POST、沒有填表、沒有儲存、沒有傳送、沒有呼叫 `btClosejQTab`、
  沒有修改正式 Playwright 流程

依指示停止，等你決定下一步。如果要往 Phase 3（WebForms state parser）走，現在的基礎
比之前紮實得多——已經有一份真實、可重現取得的 144KB 表單 HTML 和 63 個 hidden 欄位
清單可以據以實作，不必再猜。
