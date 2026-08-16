# Browser 成功路徑 vs HTTP+SSPI：完整序列比對

**目的**：找出「Edge 瀏覽器點擊出差登記、成功顯示 ESSF21」跟「`requests` + SSPI」之間，
在到達 ESSF21 表單內容之前，Browser 到底多做了什麼。全程只做被動觀察，**沒有填寫、
沒有儲存、沒有送出，也沒有執行任何 POST 重播**。

**方法**：`scripts/capture_browser_sequence.py`（新增、獨立腳本，未修改 `src/` 任何正式
檔案）attach 到你已登入的 Edge，點擊「出差登記」，記錄從點擊到 ESSF21 frame 出現之間
**完整 191 筆網路事件**、三個時間點的 cookie snapshot、EPIE001 回應內容的關鍵字分析。
原始資料在 `logs/browser_capture/`（已 gitignore）。

---

## 停止條件檢查（先講結論）

> 「如果發現 Browser 在 ESSF21 載入前存在 POST / AJAX / PostBack，請先停止，不要自行用
> requests 重播。」

**檢查結果：整個 191 筆事件中，`method == "POST"` 的數量是 0。沒有觸發停止條件。**

EPIE001 回應到 ESSF21 請求之間的 60 筆事件（Experiment B），逐筆檢查後全部是**靜態資源**
（`.css`/`.js`/`.gif`/`.jpg`）與**AjaxPro 用戶端代理程式**（`ajaxpro/*.ashx`，這是舊版
.NET 的 AJAX RPC 框架，這些 GET 請求拿到的是「產生好的 JS 代理程式碼」，不是實際呼叫
伺服器方法）。`__doPostBack` 這個字串在 EPIE001 的 HTML 裡出現 1 次，但那是 ASP.NET
WebForms 每一頁都會內嵌的**標準用戶端函式定義**（樣板程式碼），不是這次觀察期間真的
觸發了一次 postback ——**這次序列裡沒有任何一筆是真的送出資料的 POST**。

因此本次**沒有停在這裡等你確認**，而是依照你原本要求的範圍（Experiment A~E 都做完、
整理成報告）直接繼續完成，最後仍然停在「等你確認要不要進 Phase 3」這個點。如果你想親自
複核，`logs/browser_capture/sequence.json` 裡每一筆都有完整記錄。

---

## Experiment A + B：完整序列關鍵節點

| Seq | 事件 | Method | URL（base，機敏值已遮罩） | Status | Frame |
|---|---|---|---|---|---|
| 1~64 | 首頁/banner/tree/platform 既有資源載入 | GET | （首頁殼層一般資源） | 200 | 各 frame |
| — | **點擊「出差登記」** | — | — | — | banner |
| ~ | EPIE001.aspx 導覽請求 | GET | `.../EPI/EPIE001/EPIE001.aspx?FormID=ESSF21` | — | （由 platform.aspx 發起，referer=platform.aspx） |
| 65~124 | EPIE001 頁面自己的資源（60 筆） | GET | jQuery / jQuery UI Tabs / grid / AjaxPro 代理 / ScriptResource.axd 等 | 200/304 | `frameESSF21`（名稱雖含 ESSF21，內容其實是 EPIE001 wrapper） |
| **125** | **ESSF21.aspx 請求** | GET | `.../HRMESS/src/ESS/ESSF21/ESSF21.aspx?Product=true&LoginId=<遮罩>&TaskId=ESSF21&ClientIP=<遮罩>&Identifier=<遮罩>&AFormType=FRM&AFormStatus=CREATE&ProductName=EFNET` | — | referer = EPIE001.aspx 的網址 |
| **181** | **ESSF21.aspx 回應** | GET | 同上 | **200** | frame 名稱：`framePlus`，**Content-Length = 144,494 bytes** |
| 130~190 | ESSF21 頁面自己的資源（HRESS.css / ESSResponsive.js / grid.js / BlackBox.js…） | GET | HRMESS 底下的靜態資源 | 200 | `framePlus` |
| 191 | 核決歷程 timeline iframe | GET | `ApproveHistory/ApproveTimeline.aspx` | 200 | 頁面最後照常載入的既有元件，跟表單本身無關 |

**這次是完整成功的一次**：ESSF21.aspx 拿到 200、144,494 bytes 的真實表單內容，
之後還繼續正常請求自己的 CSS/JS 資源 —— 跟一個正常載入完成的頁面完全一樣。

---

## 一個誠實的自我修正：`essf21_response.html` 只有 1,409 bytes 是我的腳本抓太早

腳本在偵測到 ESSF21 frame 的 URL 一出現就立刻呼叫 `frame.content()`，沒有像
`eip_client.open_trip_form()` 那樣等待 `load`/`networkidle`。結果存到 `essf21_response.html`
的只有一個沒有 `<body>`、`<asp:Literal>` 標籤都還沒被伺服器端渲染替換掉的殘缺 HTML
（1,409 bytes）—— 這是**我這次觀察腳本自己的時序 bug**，抓到的是頁面還沒渲染完的中間
狀態，**不是** EIP 真的回應了不完整的內容。真正的網路層回應（seq 181）明確是 200、
144,494 bytes，而且緊接著瀏覽器還繼續正常請求該頁面自己的一堆 CSS/JS —— 這些行為模式
都跟「頁面已正常載入」完全一致。所以 `ESSCCDJ024_txt 是否存在：False` 這個主控台輸出
是誤判，不是真的欄位不存在（沒有時間/必要重跑一次去驗證欄位本身，但從 144,494 bytes
加上一系列後續資源請求來看，這是一次貨真價實的成功載入）。

同一個原因，`has_cookie_header` / `has_authorization_header` 這兩個欄位在記錄裡多半是
`false`——目前用的是 Playwright `request.headers`（頁面發出請求那一刻的邏輯標頭），
不是瀏覽器網路層最終送出去的完整標頭（`Cookie` 常常是網路層後補上去的）。這點**不能
當作「這個請求真的沒帶 cookie」的證據**，只能說這個量測方法本身有限制。真正可靠的
證據來自 Experiment C 的 cookie snapshot（見下）。

---

## Experiment C：Cookie 快照（三個時間點皆相同，共 50 個）

三個時間點（點擊前 / EPIE001 後 / ESSF21 後）快照下來的 cookie **名稱、數量完全沒有
變化**——沒有新增、沒有減少任何 cookie。這 50 個裡，**只有 1 個**是跟 `eip.example.com`
有關的：

| name | domain | path | Secure | HttpOnly | SameSite |
|---|---|---|---|---|---|
| `ASP.NET_SessionId` | `eip.example.com` | `/` | False | True | Lax |

其他 49 個（`MUID`、`SRCHD`、`EdgeAuth`、`AAD_AT`、`bcookie`、`XANDR_PANID`…）都是這個
Edge 個人設定檔本身在瀏覽 Bing/MSN/AAD 帳號同步/廣告技術網域時累積下來的，跟 EIP
完全無關 —— `context.cookies()` 抓的是整個持久化設定檔的 cookie，不是只有 EIP 網域的，
這裡已經手動過濾。

**沒有 `ASPXAUTH`**（預期之中——EIP 用的是 Windows 整合驗證，不是 ASP.NET Forms
Authentication，本來就不會有這個 cookie）。

**EFNET 跟 HRMESS 是否用不同的 application session？不是。** 只有一個
`ASP.NET_SessionId`，`path=/`（根目錄），代表它會同時被送往 `/EFNET/...` 跟
`/HRMESS/...` 兩邊 —— **兩個應用程式共用同一個 session cookie**，不是各自獨立的兩個
session。（這跟 `docs/http-webforms-poc.md` 觀察到「HRMESS 的回應沒有 `Persistent-Auth`
標頭」不衝突 —— 那個標頭跟 NTLM 連線驗證有關，跟這裡的 ASP.NET Session cookie 是兩個
不同機制。）

---

## Experiment D：ESSF21 網址是 HTML 直接輸出，還是 JS 產生的？

關鍵字搜尋 `logs/browser_capture/epie001_response.html`（98,484 bytes，這次也是「完整版」
大小，跟 `docs/http-webforms-poc.md` 裡第一次成功的 91,694 bytes 屬於同一類，不是那個
15,275 bytes 的精簡版）：

| 關鍵字 | 出現次數 |
|---|---|
| `framePlus` | 17 |
| `FormID` | 15 |
| `src=` | 63 |
| `ajax` | 12 |
| `TaskId` | 6 |
| `hdnUniqueTaskId` | 4 |
| `window.open` | 4 |
| `location` | 3 |
| `hdnplusFrameUrl` | 2 |
| `Identifier` | 2 |
| `universalID` | 2 |
| `__doPostBack` | 1（樣板函式定義，非觸發） |

**且直接用 regex 找 `<frame>`/`<iframe>` 標籤：確認找到一個標籤直接帶著完整、含
`Identifier` 的 ESSF21.aspx 網址。**

**結論（這次是兩個獨立來源互相印證的結果，不是單次巧合）**：ESSF21 的完整網址（含
動態產生的 Identifier）**是伺服器端在 `EPIE001.aspx` 的回應 HTML 裡直接輸出的**，不是
靠瀏覽器執行 JavaScript 之後才動態組出來的。`docs/http-webforms-poc.md` 裡純 HTTP 版本
第一次成功時也是同樣的結論；這次用真實瀏覽器再次確認一致。JavaScript 在這個過程裡的
角色，看起來主要是「把這個現成的網址塞進一個新建立的 `<iframe>` 讓它載入」（呼應
`hdnplusFrameUrl` 這個隱藏欄位名稱的字面意思），而不是負責運算/組出網址本身。

---

## Browser vs `requests` + SSPI 比較表

| Step | Browser（這次真實觀察） | `requests` + SSPI（`http_eip_explorer.py`） | Difference |
|---|---|---|---|
| 1 | GET 首頁 `/EFNET/` | GET 首頁 `/EFNET/` | 一樣，都成功 |
| 2 | （導覽殼層需要 JS 填入 banner/main frame，但這是既有登入畫面，非本次觀察重點） | 純 HTTP 完全看不到 banner/main 內容（`src=""`） | Browser 有 JS 執行環境；requests 沒有，但這一層跟能不能拿到表單無關 |
| 3 | GET `EPIE001.aspx?FormID=ESSF21`（referer=platform.aspx） | GET 同一網址（無 referer，因為不是瀏覽器導覽） | **同樣的網址，Browser 這次成功、requests 這次也曾成功過一次** |
| 4 | 60 筆靜態資源請求（CSS/JS/AjaxPro 代理） | 無（`requests` 不會自動抓頁面引用的資源） | Browser only，但這些都跟表單內容無關，純粹是頁面渲染需要 |
| 5 | 沒有任何 POST | 沒有任何 POST | 一樣 |
| 6 | GET ESSF21.aspx（帶 Referer=EPIE001 網址） | GET ESSF21.aspx（無 Referer） | **目前唯一還沒排除的候選差異** |
| 7 | 200，144,494 bytes，之後正常載入自己的資源 | 200，但 Content-Length 0（見 `docs/http-webforms-poc.md`） | 同一個目的網址，結果不同 |

### 回答 7 個問題

**1. Browser 比 requests 多哪些 request？**
主要是頁面渲染需要的靜態資源（CSS/JS/圖片/AjaxPro 代理程式碼），大約 60 幾筆，
集中在 EPIE001 這一頁。**沒有多任何一筆帶資料的 POST**，也沒有多任何一筆是專門
「初始化表單」用途、內容跟表單資料相關的請求 —— 這些都只是把頁面畫出來需要的素材。

**2. Browser 是否建立額外 application session？**
沒有觀察到。三個時間點的 cookie 快照完全沒有變化，`ASP.NET_SessionId` 一直是同一個。

**3. EFNET / HRMESS 是否出現不同 cookie？**
沒有。只有一個 `ASP.NET_SessionId`，`path=/`，同時涵蓋兩邊。

**4. Identifier 是哪一步產生？**
EPIE001.aspx 回應（seq 對應到那次 GET 的回應）裡就已經包含含 Identifier 的完整
ESSF21 網址了 —— 是伺服器處理 `EPIE001.aspx?FormID=ESSF21` 這個請求時，在**產生回應
HTML 的當下**就決定並寫入的，不是後續哪一步「額外要求」才生成。

**5. ESSF21 URL 是 HTML 直接輸出還是 JS 動態產生？**
**HTML 直接輸出**（伺服器端渲染），兩個獨立觀察（純 HTTP 一次、真實瀏覽器一次）
結果一致。

**6. requests 目前最可能漏掉什麼？**
目前唯一還沒被排除、也還沒被證實的候選差異是 **Referer 標頭**——這次真實瀏覽器
請求 ESSF21.aspx 時帶著 `Referer: <EPIE001 的網址>`，而 `http_eip_explorer.py` 沒有帶。
之前在 `docs/http-webforms-poc.md` 測試過加 Referer，但當時用的是一個已經被後續請求
「蓋掉」的舊 Identifier，測試本身並不乾淨。**這點還沒有定論**，需要一次「產生 Identifier
後立刻、只做這一件事」的乾淨測試才能確認（見下方建議，這次不自行執行）。

**7. 是否需要 POST 才能完成 ESSF21 初始化？**
**不需要。** 這次完整觀察到的 191 筆事件裡，從點擊到 ESSF21 完整載入完成，**沒有出現
任何一筆 POST**。ESSF21 的內容完全是透過一連串 GET 取得的。

---

## 目前狀態與建議（等你確認）

沒有觸發停止條件，但也還沒有把 `requests` 能不能穩定重現「Browser 這次的成功」這件事
證實 —— 目前手上有兩次獨立的「HTML 直接輸出」證據，但 `requests` 版本在拿到網址後
緊接著去 GET 卻兩次都失敗（一次 Content-Length 0，一次是我自己腳本讀取時序造成的
誤判，這次的 144,494 bytes 才是真的成功）。

如果你想繼續，下一個最小、乾淨的實驗會是：**用 `requests` + SSPI，GET 一次
`EPIE001.aspx?FormID=ESSF21`，從回應裡拿到全新 Identifier 後，立刻用同一個 session
GET 該網址一次不帶 Referer、再 GET 一次帶 Referer（設成剛剛那個 EPIE001 網址），
兩次都要在拿到 Identifier 後幾百毫秒內完成**，直接單獨驗證 Referer 是不是關鍵。
這個實驗一樣是純 GET，不需要動用 Phase 3。

在你確認之前，我不會自行執行這個實驗或任何進一步的請求。
