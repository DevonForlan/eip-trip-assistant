# HTTP + Windows SSPI 取代瀏覽器登入／操作 EIP 的可行性研究

> **⚠️ 後續更新（見 `docs/http-epie001-init-condition.md`）**
> 本文件裡「EPIE001 網址推導不可重現」以及推測的「同一使用者只能有一個建立中分頁」
> **已找到真正原因並推翻**：必要條件是同一個 session 內要先 GET 過 `CollectData.aspx`
> （`/EFNET/` 首頁的 frame src，本文件 Step 2 的爬蟲剛好走到過，所以第一次才成功；
> 之後的探測都直接打 TreeMainFrame/EPIE001，跳過了它）。加上這一步後，完整版 EPIE001
> 已可穩定重現 5/5。以下內容保留作為當時的觀察記錄。

**研究目標**：評估能否把目前的 `Edge + Playwright + CDP + 人工/半自動登入` 換成
`Python + Windows SSPI + HTTP + ASP.NET WebForms`，也就是讓 Python 直接用目前 Windows
登入者身分呼叫 EIP，不需要瀏覽器參與登入與表單操作。

**範圍**：本文件只涵蓋 Phase 1（唯讀診斷）與 Phase 2 Step 1～3（純 GET 探索）。
**沒有執行任何 POST**，沒有修改任何 AD/GPO/SPN 設定，沒有修改 `src/` 內任何正式
Playwright 程式碼。以下所有結果都是實際執行後的真實輸出，不是推測。

---

## Phase 1：驗證協定判斷（唯讀）

### 1. Kerberos Ticket（`klist`）

```
klist
```

**注意（實測發現的環境陷阱）**：這台機器的 `PATH` 裡 `klist.exe` 有兩個來源，
且 Amazon Corretto JDK 的版本排序在 Windows 系統版本**之前**：

| 來源 | 行為 |
|---|---|
| `C:\Program Files\Amazon Corretto\jdk21.0.9_10\bin\klist.exe` | Java/MIT 風格，找的是檔案型 credential cache，回報 `Credentials cache ... not found`（**誤導性錯誤，不代表沒有票證**） |
| `C:\WINDOWS\system32\klist.exe`（真正的 Windows 版本） | 查詢 Windows LSA 管理的真實票證快取，這才是瀏覽器/SSPI 實際使用的票證庫 |

改用完整路徑 `& "$env:WINDIR\System32\klist.exe"` 後，結果：

```
Cached Tickets: (2)

#0>  Client: youruser @ EXAMPLE.COM
     Server: krbtgt/EXAMPLE.COM @ EXAMPLE.COM
     （TGT，正常，代表 Kerberos 登入本身沒問題）

#1>  Client: youruser @ EXAMPLE.COM
     Server: LDAP/dc.example.com/example.com @ EXAMPLE.COM
     （曾對網域控制站做過 Kerberos LDAP 驗證）
```

**沒有任何 `HTTP/eip.example.com`（或類似）的 service ticket。**

### 2. SPN（唯讀查詢）

`setspn -Q HTTP/eip.example.com` 本身連線失敗（見下方環境限制），改用 .NET
`DirectorySearcher` 唯讀查詢 Global Catalog（連線埠 3268，非 389）得到明確結果：

```
(servicePrincipalName=HTTP/eip.example.com)  → 0 筆結果
(servicePrincipalName=*eip*)                    → 0 筆結果（整個 AD 森林都沒有）
```

**整個 AD 森林裡，沒有任何帳號登記過任何包含 "eip" 字樣的 SPN。**

**環境限制記錄**：`setspn.exe` 內部走的 LDAP 連線（埠 389）在目前網路路徑上不通
（`Ldap Error(0x51 -- Server Down)`），但 Global Catalog（埠 3268）與 SMB（埠 445）
是通的，`nltest /dsgetdc:` 也能正常定位到 `dc.example.com`（10.0.0.10）。也就是說
不是網域連不上，是 `setspn.exe` 這個工具本身慣用的連線方式在目前網路環境下不通，
改用 GC 查詢繞過後就能拿到結果 —— **這不是修改任何設定，純粹是換一個唯讀查詢的路徑**。

### 3. Edge Policy（待人工確認）

`edge://policy` 的 `AuthServerAllowlist` / `AuthSchemes` 這兩項目前**還沒有請你回報**。
不過下面 Phase 2 Step 0 的實測結果（伺服器直接回應 `WWW-Authenticate: Negotiate, NTLM`）
已經足以回答「伺服器支援什麼」這個問題；`edge://policy` 只補「瀏覽器端政策設定」這一小塊，
若之後還想確認可以隨時提供。

### 判斷結論：Kerberos 還是 NTLM？

**結論：NTLM。** 這不是猜測，是三個獨立證據互相印證：

1. AD 裡完全沒有 `HTTP/eip.example.com` 或任何含 "eip" 的 SPN → Kerberos **結構上不可能**
   對這個服務發出 service ticket（KDC 找不到對應的 principal）。
2. `klist` 顯示這個登入 session 從來沒拿到過 HTTP/eip 的票證，即使已經用同一個身分多次
   操作 EIP。
3. 伺服器對匿名請求回應 `WWW-Authenticate: Negotiate, NTLM`（Phase 2 Step 0 實測）——
   有提供 Negotiate 是正常的 IIS 預設行為，但因為 #1 的關係，Negotiate 協商必然會
   降級成 NTLM，不會真的走到 Kerberos。

---

## Phase 2：HTTP + SSPI Explorer（`scripts/http_eip_explorer.py`）

腳本只做 GET，會把結果印到主控台，並把結構化結果（機敏欄位已遮罩/僅保留長度）存到
`logs/http_explorer/findings.json`，原始 HTML 快照存在同目錄（都已 gitignore）。

執行：`python scripts/http_eip_explorer.py`

### Step 0：匿名請求觀察驗證機制

| 項目 | 結果 |
|---|---|
| 狀態碼 | 401 |
| `WWW-Authenticate`（僅方案名稱，未記錄完整標頭值） | `Negotiate`, `NTLM` |

### Step 1：SSPI 驗證 GET 首頁

| 項目 | 結果 |
|---|---|
| 狀態碼 | 200（穩定成功，多次執行、跨 3 次獨立腳本執行皆成功，**零次驗證失敗**） |
| 最終網址 | `http://eip.example.com/EFNET/`（無多餘重新導向，401→401→200 是 SSPI 內部的挑戰-回應交握，非應用層重新導向） |
| Content-Type | `text/html` |
| 回應標頭 `Persistent-Auth` | `true`（跟先前 SSPI 實驗一致：這一層驗證是綁在連線本身） |
| Set-Cookie | 沒有出現在 EFNET 首頁回應中 |
| Frame 數 | 1（`TreeMainFrame.aspx`） |

**額外發現（追加探測時發現）**：繼續往下爬到 `TreeMainFrame.aspx` 時，伺服器**有**
核發一顆 `ASP.NET_SessionId` cookie（僅記錄名稱，不記錄值）。也就是說整個站點不是
完全無狀態 —— 前台 EFNET 這一層確實有走傳統 ASP.NET Session。

### Step 2：Frame 樹狀結構（純 HTTP，不執行 JavaScript）

實際爬到的結構：

```
/EFNET/  (1 個 frame)
└─ TreeMainFrame.aspx  (5 個 frame)
   ├─ banner   → src=""  ⚠️ 空的
   ├─ contents1 → tree.aspx        ✅ 200
   ├─ marquee   → Marquee.aspx     ✅ 200
   ├─ main     → src=""  ⚠️ 空的
   └─ contents3 → ShowStatus.aspx  ✅ 200
```

（`banner`／`main` 的空白 src 是追加探測直接讀原始 HTML 標籤確認的：
`<frame name="banner" id="banner" ... src="" scrolling="no">`，`main` 同樣。）

**這是本次研究最重要的結構性發現**：不是只有「出差登記」那個分頁需要 JavaScript
才能生成 —— **連最外層的導覽殼（banner 選單列、main 內容區）本身的 frame src
都是空的，必須靠頁面載入後的 JavaScript 動態填入**，純 HTTP GET 完全看不到
`platform.aspx`、更看不到 `EPIE001.aspx`／`ESSF21.aspx`（這三者在 Step 2 的爬蟲結果
中都是 `False`，符合預期，因為它們本來就不在伺服器端渲染的初始 HTML 裡）。

### Step 3a：直接 GET 使用者指定的裸路徑

```
GET http://eip.example.com/HRMESS/src/ESS/ESSF21/ESSF21.aspx
→ 302 → http://eip.example.com/HRMESS/src/_Common/AppUtil/FrameSet/SessionTimeOut.aspx
→ 200, title = "SessionTimeout"
```

沒有拿到 401（代表 Windows 驗證本身沒問題），但應用程式層認定這個請求「沒有有效狀態」，
導回逾時頁 —— 符合預期，因為完全沒帶任何 `LoginId`/`TaskId`/`Identifier` 等參數。

也發現一個結構性事實：`HRMESS`（放 `ESSF21.aspx` 的地方）跟 `EFNET`（放
`EPIE001.aspx` 的地方）是**兩個完全不同的 ASP.NET 應用程式**——`X-AspNet-Version`
分別是 `2.0.50727`（HRMESS，很舊）跟 `4.0.30319`（EFNET）。而且 HRMESS 這邊的回應
從來沒出現過 `Persistent-Auth` 標頭。這對後續判斷「為什麼拿不到表單內容」很關鍵，
細節見下方 Step 3c 的討論。

### Step 3b：從已知穩定進入點推導 ESSF21.aspx 網址（不硬編、不猜測）

固定進入點：`http://eip.example.com/EFNET/src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21`
（這個網址本身沒有任何 session 專屬參數，跟專案裡引用 CSS selector id 一樣，是穩定的
應用程式進入點，不是猜測或硬編某個使用者的 session 資料）。

**第一次執行（腳本主流程，收錄在 `findings.json`）：成功**

- 回應大小 91,694 bytes
- 直接在回應 HTML 裡找到：`<frame ... src="HRMESS/src/ESS/ESSF21/ESSF21.aspx?Product=true&LoginId=E12345&TaskId=ESSF21&ClientIP=10.0.0.20&Identifier=0123456789abcdef0123456789abcdef&AFormType=FRM&AFormStatus=CREATE&ProductName=EFNET">`
- 這個網址是**從實際回應內容抓出來的**，`Identifier` 是伺服器當次動態產生的（跟
  `docs/eip-analysis.md` 裡透過瀏覽器觀察到的另一個 `Identifier` 值不同，確認這個值
  確實是每次動態生成，不是固定值）。

**追加驗證：重複執行 5 次，全部失敗（不可重現）**

之後為了驗證這個結果是否穩定，額外執行了 5 次同樣的 GET（含首次追加探測與
`Q3` 的 4 次重複測試）：

| 次數 | 回應大小 | 內文含 ESSF21.aspx |
|---|---|---|
| 第 2 次 | 15,275 bytes | 否 |
| 第 3 次 | 15,275 bytes | 否 |
| 第 4 次 | 15,275 bytes | 否 |
| 第 5 次 | 15,275 bytes | 否 |
| 第 6 次 | 15,275 bytes | 否 |

**這個網址推導能力目前不可靠重現** —— 只在「第一次」成功過一次，之後穩定地回應
一個小很多、不含 ESSF21 連結的版本。目前最可能的假設（尚未證實）：EPIE001.aspx
背後可能有「同一個使用者/同一個表單類型，同時只能有一個建立中的分頁」這類伺服器端
狀態鎖 —— 第一次呼叫觸發「開新分頁」邏輯並回傳完整內容，後續呼叫偵測到「已經開過」
就回傳精簡版。這跟另一份調查報告（`docs/login-automation-investigation.md`）裡
Chromium 對 CDP 導覽的封鎂**性質完全不同** —— 那是瀏覽器引擎層級、無條件的安全邊界；
這裡看起來更像**應用程式自己的業務邏輯狀態**，原則上可能有辦法繞過或重置，但目前
還沒找到觸發條件，需要更多實驗才能確認（見下方「下一步最小實驗」）。

### Step 3c：GET 推導出的網址，檢查表單欄位

**兩次嘗試（原始執行 + 使用同一網址的追加重試），結果一致：**

```
狀態碼：200
Content-Length：0
Content-Type：（空，完全沒有這個標頭）
```

**伺服器回了一個完全空白的 200**，不是錯誤頁、不是重新導向。額外測試加上
`Referer`（模擬瀏覽器載入子 frame 時會帶的標頭）、加上瀏覽器樣式的 `User-Agent`、
加上 `Sec-Fetch-Dest: iframe` 等標頭，結果都一樣是空白 200 —— **這幾個標頭不是
決定性因素**。

比較合理的解讀（結合 Step 3b 的不可重現性一起看）：這個 `Identifier` 值本身很可能
是**單次有效或極短時效**的權杖，Step 3b 生成它、Step 3c 緊接著去用它時就已經失效了
（同一次腳本執行內、間隔不到 1 秒就已經如此），而不是缺少某個特定 HTTP 標頭的問題。
**目前為止，還沒有一次成功「讀到 ESSF21.aspx 真正的表單內容」**，因此
`ESSCCDJ024_txt` 等欄位、`__VIEWSTATE` 等 WebForms 隱藏欄位的存在性，這次都還沒能
用純 HTTP 的方式確認 —— Phase 2 Step 3 在這一點上是**尚未成功**，不是失敗，是「卡在
一個看起來可解、但還沒解開的狀態時效問題」。

---

## 回報：使用者指定的 8 個問題

**1. EIP 實際使用 Kerberos 還是 NTLM？**
NTLM。AD 裡沒有任何 `HTTP/eip*` 的 SPN（結構上排除 Kerberos），`klist` 從未出現過
對應票證，伺服器雖提供 `Negotiate` 但必然降級為 NTLM。三個獨立證據互相印證，判斷
可信度高。

**2. SSPI 是否穩定取得首頁？**
是，非常穩定。3 次獨立腳本執行、共 8 次以上請求，全部 SSPI 驗證成功、零次失敗、
零次逾時。這跟另一份報告記錄的「CDP 驅動的 Edge 登入會反覆在成功/失敗間跳動」明顯
不同 —— **純 HTTP + SSPI 在登入這一步，目前看起來比瀏覽器路線穩定得多**。

**3. 是否能沿 frame 結構取得 ESSF21？**
部分可以，但不穩定。首頁本身的導覽殼（banner/main）就需要 JavaScript 才能填入
內容，純 HTTP 完全看不到；但往下一層、直接打已知的 `EPIE001.aspx?FormID=ESSF21`
進入點，第一次真的成功從伺服器回應中拿到一個完整、動態產生、非猜測的 ESSF21.aspx
網址 —— 證明這條路徑理論上不需要 JS 就能走通，但重複執行 5 次都無法再現，懷疑
跟「同一使用者只能有一個建立中分頁」之類的伺服器端狀態有關。

**4. 是否能讀到真正的表單欄位？**
還沒有。唯一一次成功推導出的網址，緊接著去 GET 時拿到的是空白的 200
回應（Content-Length: 0），加上 Referer/User-Agent/Sec-Fetch 標頭都無法改變結果。
目前判斷比較可能是這個網址裡的 `Identifier` 屬於單次有效/極短時效的權杖，而不是
缺少某個標頭。

**5. 是否能解析 ASP.NET hidden state？**
還沒機會驗證 —— 因為 #4 還沒拿到含表單內容的回應，`__VIEWSTATE` 等欄位目前查到的
都是「不存在」，但那是因為回應本身是空的，不代表這個技術路徑本身不能用。

**6. 目前 HTTP 自動化可行性評估？**
分兩層來看：**登入/驗證層，可行性高** —— SSPI 拿到的存取跟真人瀏覽器等價，且比
CDP 路線穩定；**深入到特定表單內容這一層，可行性未定** —— 卡在一個看起來是應用程式
業務邏輯（而非安全邊界）的狀態管理問題，性質上比「Chromium 封鎖 CDP 導覽的 NTLM
SSO」更有機會找到解法，但需要更多針對性實驗才能確認，不能現在斷言可行或不可行。

**7. 下一步最小實驗應該做什麼？**
建議三個都還是純觀察/GET 性質、成本低的實驗（任一項都不需要動到 POST 或正式流程）：
   - **(a) 用現有 Playwright/NetworkRecorder 觀察一次真人點擊「出差登記」時，瀏覽器
     實際發出的、載入 framePlus 這個 frame 的那一個請求**（只是被動觀察真實瀏覽器的
     行為，不涉及送出表單），確認真的沒有帶什麼我們沒注意到的標頭或 cookie。
   - **(b) 縮短 Step 3b→3c 之間的間隔到接近 0**（目前已經很快，但可以用同一個
     TCP 連線內的 pipeline 或至少確認沒有中間商），排除「單純是我們自己太慢」這個
     最簡單的可能性。
   - **(c) 測試「連續兩次呼叫 EPIE001.aspx 之間，如果先呼叫 `btClosejQTab`
     對應的後端邏輯（如果有獨立的 URL），是否能讓下一次 GET 重新拿到完整內容」**——
     直接驗證「單一分頁鎖」假設是否成立。

**8. 是否仍有必要研究 CDP 登入？**
是，現階段仍需要保留。CDP 路線目前是唯一「曾經完整走到送出表單並成功」的路徑，
HTTP/SSPI 路線目前只證明了「登入層可行且更穩定」，還沒有證明「能穩定讀到表單、
更別說填表送出」。兩條線應該繼續並行、互不影響 —— 這次的探索完全沒有修改
`src/` 裡任何正式檔案，Playwright/CDP 路線原封不動。

---

## 目前狀態

Phase 1 + Phase 2 Step 1～3 已完成，依指示在此停止，**不進入 Phase 3（WebForms
state parser）、不對任何頁面送出 POST**，等待進一步指示。
