# EIP 自動登入調查報告

> ## ⚠️ 2026-08-14 重大更正：本文件的核心結論已被推翻
>
> **問題已經解決了。** 只要在啟動 debug Edge 時加上一個參數：
>
> ```
> --auth-server-allowlist=*.example.com
> ```
>
> 實測結果：`browser.attach_context()` **3.4 秒完成自動登入，零人工介入、不出現任何認證框**。
> 這個參數已加進 `src/browser.py` 的 `edge_launch_args()`。
>
> **原本的誤判**：本文件把反覆出現的 `chrome-error://chromewebdata/` 判斷為
> 「Chromium 內部 NTLM 協商不穩定」、「持續在成功/失敗間跳動」，並據此結論「純軟體無法
> 達到 100%，只能靠 IT 設定 Kerberos 限制委派」。
>
> **真正的原因**：這個專案專用的 `.edge-profile` 沒有繼承使用者平常 Edge 的自動 SSO
> 白名單設定，所以 Chromium 拒絕自動送出 Windows 認證，改為彈出原生的「Windows 安全性」
> 認證對話框。自動化執行時沒有人回應那個對話框 → 請求未通過驗證 → 分頁落到錯誤頁。
> 我先前觀察到的「成功/失敗跳動」，其實是那個對話框的出現與消失，不是網路層問題。
>
> **為什麼下方第 2 節說這個參數「無效」**：因為當時測的是**完全不同的問題**——Playwright
> 用 `page.goto()` 主動導覽被 Chromium 封鎖，那個限制跟白名單無關，加什麼參數都沒用。
> 兩件事被混為一談，這是本次調查最大的方法論失誤。
>
> 下方第 2 節與「結論」一節關於「必須靠 IT 基礎設施」的部分**不再適用**。
> 其餘章節（CDP 導覽封鎖、SSPI 連線綁定、pywinauto 前景鎖等）的觀察仍然有效。

**調查目的**：EIP 使用 Windows 整合驗證（NTLM/Negotiate），一般手動開啟 Edge 完全不需要輸入密碼即可登入，但透過 Playwright 自動化工具卻始終無法自動完成登入。本文件記錄整個調查過程中嘗試過的**所有**方法、每個方法的結果、以及背後的技術原因。

**結論先講**：目前找到唯一部分有效的方法（外部啟動瀏覽器＋網址當命令列參數＋事後用 CDP 附加），但**無法達到 100% 穩定**，且已透過 9 種不同的技術角度反覆驗證排除了其他可能性。真正能做到 100% 免人工介入的方法，需要 IT／網域管理員在基礎設施層級設定（Kerberos 限制委派的服務帳號），不是單靠腳本能達成。

---

## 背景：問題的本質

EIP 是舊式 ASP.NET／IIS 系統，使用 **Windows 整合驗證**：登入身分是「目前這台電腦已登入的 Windows 帳號」，透過 NTLM 或 Negotiate（Kerberos）協定跟伺服器做網路層級的握手，**沒有網頁登入表單、沒有帳號密碼輸入框**。這也是為什麼一般開 Edge 完全無感登入的原因。

問題出在：Chromium（Edge、Chrome 背後的引擎）團隊刻意設計了一個安全機制——**只要一個瀏覽器分頁是透過 CDP（Chrome DevTools Protocol，Playwright／Puppeteer 等自動化工具用來遠端控制瀏覽器的協議）被接管過，這個分頁上發生的任何導覽，都不會觸發自動 NTLM/Negotiate SSO**。這是為了防止惡意自動化程式偷用使用者目前的 Windows 身分，未經同意存取內部系統——是刻意的安全邊界，不是 bug。

---

## 嘗試過的方法一覽

| # | 方法 | 結果 | 根本原因 |
|---|---|---|---|
| 1 | Playwright 直接 `launch()` + `page.goto()` | ❌ 失敗（`ERR_INVALID_AUTH_CREDENTIALS`） | CDP 導覽一律被擋 |
| 2 | 加 `--auth-server-whitelist` 命令列參數強制 SSO | ❌ 失敗，同樣錯誤 | whitelist 只影響「要不要嘗試自動 SSO」，不影響 CDP 導覽本身被擋這件事；失敗後也不會退回顯示原生登入框 |
| 3 | `connect_over_cdp()` 附加到「外部啟動、網址當命令列參數」的 Edge | 🟡 **部分成功，不穩定** | 導覽發生在 Playwright 接管前，能觸發 SSO；但成功率受當下網路/Chromium 內部協商時序影響，觀察到會在成功/失敗間反覆跳動 |
| 4 | 模擬「真人點擊連結」取代 `.goto()`（測試是否跟使用者手勢有關） | ❌ 失敗，同樣錯誤 | 證實限制跟「導覽方式」無關，是「分頁是否曾被 CDP 接管」——接管後任何導覽方式都被擋 |
| 5 | `launch_persistent_context(channel="msedge")` 啟動**真正的** Microsoft Edge | ❌ 失敗，同樣錯誤 | 證實限制跟「是否為真正 Edge」「是否吃到公司 GPO 政策」都無關，只跟「導覽是否由 Playwright 發起」有關 |
| 6 | OS 層級鍵盤模擬（`pywinauto`／Windows UI Automation）操控已開啟視窗的網址列 | ❌ 失敗（`SetForegroundWindow` 未生效） | Windows 有安全限制：非使用者主動操作、由背景程式呼叫的搶前景視窗焦點常被系統忽略，防止惡意程式偷走使用者目前操作的視窗焦點 |
| 7 | `requests_negotiate_sspi`：用 Windows SSPI 直接發 HTTP 請求（完全不透過瀏覽器） | 🟡 **HTTP 驗證本身 100% 成功**，但無法沿用到瀏覽器 | 伺服器回應 `Persistent-Auth: true`、無 `Set-Cookie`——驗證狀態綁在 TCP 連線本身，不是 cookie/token，沒有「東西」可以拿去交給瀏覽器沿用 |
| 8 | 用 WMI（`Win32_Process.Create`）取代 `subprocess.Popen` 啟動瀏覽器（排除行程鏈本身的影響） | ❌ 失敗，跟原本方式一樣不穩定 | 排除「行程建立方式／父行程鏈」是造成不穩定的原因 |
| 9 | 加大重試次數、觀察多次啟動結果的穩定性模式 | 🟡 觀察到**持續在成功/失敗間反覆跳動**（10~15 秒週期），不是「重試幾次後穩定」 | 底層有某種持續協商/重試機制，問題本質是即時的網路/驗證協商狀態，不是單純的「一次性失敗，多等一下就好」 |

另外檢查並排除：
- **Edge 安全 DNS（DoH）設定**：檢查 profile 設定檔，沒有明確啟用，預設模式下不太可能是主因。
- **網路連通性本身**：透過 `nslookup`、`curl`、SSPI 請求反覆確認，網路路徑（VPN／DNS）本身一直是通的，問題不在連通性。

---

## 各方法詳細說明

### 方法 1～2：直接導覽 / 命令列白名單

最初的嘗試：用 Playwright 自己啟動瀏覽器，呼叫 `page.goto(EIP_URL)`。結果立即得到：

```
playwright._impl._errors.Error: Page.goto: net::ERR_INVALID_AUTH_CREDENTIALS
```

加上 `--auth-server-whitelist=*.example.com --auth-negotiate-delegate-whitelist=*.example.com` 命令列參數（這是一般企業用 GPO 讓瀏覽器自動 SSO 的機制）後，結果一樣失敗。這代表：即使明確告訴 Chromium「這個網域可以自動用 Windows 身分登入」，只要是 CDP 控制的分頁，這個授權也不會被套用。

### 方法 3：外部啟動＋事後接管（目前唯一部分有效的方法）

改變思路：不讓 Playwright 發起導覽，而是用一般的 `subprocess.Popen` 啟動 `msedge.exe`，把目標網址當成**命令列參數**直接帶入：

```
msedge.exe --remote-debugging-port=9222 --user-data-dir=<profile> "http://eip.example.com/EFNET/"
```

這個導覽是作業系統／瀏覽器自己的行程啟動邏輯處理的，不經過 CDP，所以 SSO 可以正常觸發。等瀏覽器完成登入後，才用 `playwright.chromium.connect_over_cdp()` 接上去讀取/操作 DOM。

這個方法**證實可行**（今天已有多次成功案例，包含兩筆真實出差登記送出成功），但**不穩定**：同樣的指令，有時候幾秒內成功，有時候會卡在暫時性錯誤畫面（`chrome-error://chromewebdata/`），甚至觀察到同一個分頁會在成功/失敗兩個狀態之間反覆跳動長達 10~15 秒以上才可能穩定下來（或持續不穩定）。

### 方法 4：真人手勢測試

假設：也許限制的判斷條件是「這次導覽有沒有真人手勢觸發」，而不是「CDP 本身」。測試方法：在一個已被 Playwright 接管的分頁裡，不呼叫 `.goto()`，改用 Playwright 的 `.click()` 模擬點擊一個真實的 `<a href>` 連結（`.click()` 底層是送出真正的滑鼠事件，跟真人點擊在協定層級上更接近）。

結果：一樣失敗，同樣的 `ERR_INVALID_AUTH_CREDENTIALS`。

**結論**：限制的判斷條件不是「這次導覽是不是模擬的」，而是「這個分頁本身有沒有被 CDP 接管過」——一旦 Playwright 連上了某個分頁，之後**任何**導覽方式（無論是 `.goto()` 還是模擬點擊）都會被擋。這也解釋了為什麼「先用真人打開、登入後才接管」的順序缺一不可：接管之後就回不去了。

### 方法 5：真正的 Microsoft Edge

假設：也許限制只針對 Playwright 內建的 bundled Chromium，如果用 Playwright 的 `channel="msedge"` 參數啟動系統上**真正安裝的** Microsoft Edge（會吃到公司 GPO 政策），情況會不同。

測試：`playwright.chromium.launch_persistent_context(user_data_dir=..., channel="msedge", headless=False)`，然後呼叫 `page.goto(EIP_URL)`。

結果：一樣失敗，同樣的 `ERR_INVALID_AUTH_CREDENTIALS`，連截圖都是空白錯誤畫面。

**結論**：限制跟「是不是 bundled Chromium」、「有沒有吃到 GPO 政策」都無關。只要導覽是 Playwright 發起的，不管背後執行的是哪個瀏覽器執行檔，一律被擋。這也代表：即使之後想把 `connect_over_cdp()`（官方文件承認 fidelity 較低）換成更「正規」的連線方式，也沒辦法藉此繞過 NTLM 這道牆，因為牆本身跟連線方式無關。

### 方法 6：OS 層級鍵盤模擬

思路：如果連「模擬點擊」都不算真人手勢，那改用完全在 CDP 之外的輸入方式——透過 Windows 的 UI Automation API（`pywinauto`），直接對已經開啟的瀏覽器視窗送出「按 Ctrl+L 聚焦網址列 → 輸入網址 → 按 Enter」，這是作業系統層級的鍵盤事件，理論上跟真人操作在系統層級無法區分。

測試步驟：
1. 用 `pywinauto.Application.connect(process=<pid>)` 連到目標視窗
2. 呼叫 `win32gui.SetForegroundWindow(hwnd)` 把視窗設為前景
3. 用 `pywinauto.keyboard.send_keys()` 送出按鍵

結果：`SetForegroundWindow` 沒有真正生效——UI Automation 回報該視窗元素「未啟用」（`ElementNotEnabled`），送出的鍵盤事件沒有反映到畫面上。

**原因**：Windows 有一個刻意的安全限制——**非使用者主動操作、由背景程式呼叫的 `SetForegroundWindow` 常常會被系統忽略或不完全生效**。這是為了防止惡意程式偷走使用者目前正在操作視窗的焦點（例如彈出一個假視窗騙你輸入密碼）。我們的 Python 程式是從終端機／背景程序啟動的，沒有「使用者剛剛操作過」的資格去搶奪其他視窗的前景焦點，所以即使呼叫了 API，系統也不會真的把焦點/輸入導向目標視窗。

### 方法 7：SSPI 直接發 HTTP 請求

思路：NTLM/Negotiate 本來就不是瀏覽器專屬的功能，是 Windows 作業系統的 SSPI（Security Support Provider Interface）機制。用 `requests_negotiate_sspi` 套件，讓 Python 用目前登入的 Windows 身分直接對 EIP 發送 HTTP 請求，完全不透過瀏覽器：

```python
import requests
from requests_negotiate_sspi import HttpNegotiateAuth

session = requests.Session()
session.auth = HttpNegotiateAuth()
resp = session.get("http://eip.example.com/EFNET/")
```

結果：**HTTP 請求本身完全成功**（狀態碼 200，不是 401 未授權）。但檢查回應標頭發現：

```
Persistent-Auth: true
```

且**完全沒有 `Set-Cookie`**。

**原因**：這證實 EIP 的登入驗證是**綁在這一條 TCP 連線本身**（IIS 的 NTLM Persistent Authentication 機制），不是透過 cookie 或 token 追蹤 session。也就是說，就算我這邊用 SSPI 驗證成功了，也沒有任何「東西」可以拿去交給 Playwright 開的瀏覽器沿用——沒有 cookie 可以塞進 `context.add_cookies()`，沒有 token 可以複製。驗證狀態完全綁死在那一條連線上，連線一結束（Python 程式退出）驗證狀態就消失了。這是一個乾淨的**技術性否定結果**：確認這條路完全走不通，不是沒試成功、是根本沒有可轉移的東西。

### 方法 8：WMI 行程建立

思路：懷疑會不會是我們啟動瀏覽器的方式本身有問題——目前是透過「終端機工具 → Git Bash → Python → `subprocess.Popen`」這一條很深的巢狀行程鏈啟動 `msedge.exe`，也許某種環境變數或權杖繼承的細節影響了 Chromium 判斷這個啟動是否「可信」。改用 Windows 管理工具（WMI）的 `Win32_Process.Create` 方法啟動，讓新行程的父行程是 WMI Provider Host（一個完全不同的系統服務），而不是我們的 shell：

```powershell
Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine = "..."}
```

結果：一樣不穩定，跟原本用 `subprocess.Popen` 啟動的結果沒有差異。

**結論**：排除了「行程建立方式／父行程鏈」是造成不穩定的原因。問題不在我們怎麼啟動這個行程，而是啟動之後，Chromium 內部處理 NTLM/Negotiate 協商的過程本身有時序上的不穩定性。

### 方法 9：加大重試次數與觀察穩定性模式

最後測試：把「啟動失敗就整個關掉重開」的重試邏輯多跑幾輪，並且**連續多次檢查同一個分頁的狀態**，觀察它是「一次性失敗後穩定」還是「持續變動」。

結果：觀察到同一個分頁會在「正確網址」跟「`chrome-error://chromewebdata/`」兩個狀態之間**反覆跳動**，跳動的時間跨度超過 10～15 秒，且下一次檢查很可能又跳回錯誤狀態，不是單純「一次性失敗，多等等就會穩定成功」的模式。

**結論**：這代表底層有某種持續在進行的重試或重新協商機制（可能跟 Windows 網域控制站的回應時間、Kerberos ticket 快取狀態、本機網路介面切換等因素有關），問題本質是**即時的網路/驗證協商狀態**，這些都是從 Python 腳本外部無法觀測、也無法控制的黑盒子行為。單純加大重試次數或延長等待時間，沒辦法保證解決，只能提高「碰巧撞到穩定窗口」的機率。

---

## 為什�麼「連續嘗試很多次」不是好的解法

值得特別說明：雖然理論上「重試次數夠多，總有一次會成功」，但這裡刻意沒有採用「無限重試直到成功」的策略，原因：

1. **對公司網路/伺服器不必要的負擔**：短時間內大量重複的 NTLM 驗證嘗試，即使沒有觸發任何鎖定機制（已確認沒有），也不是良好的網路公民行為。
2. **無法區分「快成功了」跟「這次環境本來就不行」**：觀察到的反覆跳動模式代表沒有一個穩定的訊號可以判斷「再等一下就會好」還是「今天環境就是不行」，盲目重試可能是在浪費時間。
3. **跟目的不成比例**：登入自動化本身不是使用者的最終目標，出差申請的送出才是。當自動登入卡住時，手動登入一次只需要幾秒鐘，比繼續讓程式重試更有效率。

---

## 結論與唯一真正的 100% 解法

**目前結論**：透過純軟體／腳本層面的手段，無法保證 100% 免人工介入完成登入。已經從 9 個不同的技術角度驗證過，包括：導覽方式（直接/模擬點擊）、瀏覽器種類（bundled Chromium/真正 Edge）、連線層級（CDP/SSPI 原生 HTTP）、輸入方式（CDP/OS 鍵盤模擬）、行程建立方式（subprocess/WMI）。每一種都得到明確的失敗原因，不是「還沒找到正確方法」，而是**已經確認這些方法在架構上就是走不通**。

真正能做到 100% 自動化、不需要任何人工介入的方法，需要 **IT／網域管理員在基礎設施層級設定**：讓一個服務帳號（Service Account）透過 **Kerberos 限制委派（Constrained Delegation）** 取得存取 EIP 的合法權杖。這種做法完全不需要開瀏覽器 UI，也不需要任何人手動登入，是企業 RPA（機器人流程自動化）常見的標準做法，但需要 AD／伺服器端的設定變更，不是單靠寫 Python 腳本能達成的，需要另外跟 IT 部門討論。

---

## 目前實務上的處理方式（已實作）

在等待可能的基礎設施層級方案之前，目前程式碼採用「盡力自動、失敗優雅退回手動」的策略：

- `browser.attach_context()` 會自動嘗試啟動並等待登入穩定（含重試機制）
- 如果自動化在時限內沒有成功，會清楚印出手動指令，讓使用者自己開瀏覽器登入一次
- 登入完成後，後續所有操作（開表單、填資料、查重複、送出、驗證結果）都是完全自動化的，只有「登入」這一個步驟偶爾需要人工介入
