# EIP 出差登記自動化工具

自動填寫並送出企業 EIP（Digiwin EasyFlow / ERPII Plus 系列）的「出差登記」表單。

Python + Playwright 驅動一個已登入的 Edge；另有一條純 HTTP + Windows SSPI 的路線可
直接讀取表單，不需要瀏覽器。

> **設定檔全部是佔位符。** 程式碼與文件中的主機名稱、員工編號、單據編號、內網 IP
> 一律是 `example.com` 這類 RFC 2606 佔位值。要對接真實系統必須自行建立 `.env`。

---

## 為什麼這件事沒有想像中簡單

這類舊式 ASP.NET WebForms 系統有幾個一般自動化教學不會提到的陷阱，本專案都實測過並
記錄在 `docs/`：

| 問題 | 結論 |
|---|---|
| Playwright 開的瀏覽器連不上（`ERR_INVALID_AUTH_CREDENTIALS`） | Chromium 刻意封鎖「被 CDP 接管過的分頁」自動完成 NTLM SSO。解法是把網址當**啟動參數**傳給瀏覽器，之後才 attach |
| 專用 profile 一直跳 Windows 認證框 | 缺 `--auth-server-allowlist`。加上就完全自動登入 |
| 純 HTTP 取表單只拿到精簡版 | 同一個 session 必須先 GET 過 `CollectData.aspx`。有 SessionId **不代表**初始化完成 |
| 表單回應 200 但 0 bytes | 缺 `Accept-Language`。頁面有 I18N 邏輯，判斷不出語言就整個不輸出 |
| `__VIEWSTATE` 是空的 | 這套系統用自有的 `__MSPVSTATE`（壓縮）取代標準 ViewState |
| 「儲存」按鈕的真實提交機制 | 不是那顆按鈕、也不是 `__doPostBack`，而是一個 0 像素隱藏的 `<input type="image">` |
| CDP 連線握手成功後卡住 | 長時間執行的 debug Edge 會進入「websocket 接得上、但列舉 target 卡死」的狀態。已內建偵測與自動重啟 |
| 表單追蹤清單顯示的是舊資料 | 瀏覽器的原稿資料匣會給出快取結果，漏掉剛建立的單據。重複檢查因此同時查詢瀏覽器與獨立的 HTTP 來源 |

完整調查過程見 [`docs/`](docs/)。

---

## 安裝

```powershell
pip install -r requirements.txt
playwright install chromium
```

Windows 專用：登入依賴 Windows 整合驗證（NTLM/Negotiate）與 SSPI。

## 設定

```powershell
copy .env.example .env
```

編輯 `.env`，只有 `EIP_URL` 是必填——其他主機名稱都由它推導：

```
EIP_URL=http://your-eip-host/EFNET/
EIP_AUTH_ALLOWLIST=*.your-domain
```

`.env` 已列入 `.gitignore`。**本工具從不讀取、儲存或傳送密碼**，登入一律由瀏覽器
以 Windows 整合驗證完成。

## 使用

```powershell
python src/main.py
```

會依序詢問出差日期、時間、地點、事由等，然後：

1. 顯示輸入摘要 → 需要輸入 `y` 才繼續
2. 自動啟動並登入 Edge、開啟表單、填入資料
3. 查詢「表單追蹤處理」是否已有相同日期的單據，**有就中止**
4. 加入出差人
5. **把瀏覽器畫面上的實際內容讀回來顯示** → 再輸入一次 `y` 才會點擊「傳送」

任何一次輸入非 `y` 都會立即停止，表單留在畫面上不送出。

## 安全設計

這個工具會執行**無法復原**的正式送件動作，所以刻意做了幾層限制：

- **兩段式確認**：送出前會把瀏覽器上的實際欄位值讀回顯示，而不是回放你輸入的變數
- **重複送出防護**：送出前同時查詢瀏覽器畫面與獨立的 HTTP 來源（瀏覽器的清單會給出快取的
  舊資料），任一來源發現相同日期/時間的單據就中止
- **明確狀態機**（`src/state_machine.py`）：session 過期是硬性中止，且**任何情況都不自動重送**
- **對話框分類處理**（`src/dialog_handler.py`）：beforeunload 自動接受；confirm 只在訊息不含
  「已存在／重複／覆蓋／錯誤／失敗」等關鍵字時接受；alert/prompt 一律不自動接受
- **送出結果驗證**（`verify_submission`）：以單據編號與唯讀導向為準，不用「畫面變空白」判斷成功。
  結果為 UNKNOWN 時明確要求人工確認，禁止重送
- **HTTP 路線預設唯讀**：`HttpEipClient` 的 `post/put/patch/delete` 直接擋掉，要改狀態必須
  明確傳 `read_only=False`
- **記錄一律遮罩**：Authorization/Cookie 不記錄；POST 只記欄位名稱與長度，不記值
- **連線自我復原**：CDP 連線卡住時自動重啟瀏覽器並重試一次，但只重試一次——重啟後仍失敗代表問題不在瀏覽器，繼續重試只會拖延到人發現

## 專案結構

```
src/
  config.py          # 集中設定，載入 .env（所有主機名稱由 EIP_URL 推導）
  browser.py         # VPN 檢查、啟動 debug Edge、CDP attach
  eip_client.py      # 導覽 EIP、開啟/關閉出差登記表單
  trip_form.py       # 填表、加入出差人、送出、驗證結果
  duplicate_check.py # 查詢原稿資料匣，防止重複送件
  session.py         # 登入狀態判定
  state_machine.py   # 流程狀態機（SESSION_EXPIRED 為硬性中止）
  dialog_handler.py  # 對話框分類處理
  network_log.py     # 網路記錄（含遮罩）
  main.py            # 互動式 CLI 入口

  http_eip_client.py # 純 HTTP + SSPI 路線（預設唯讀）
  webforms_state.py  # ASP.NET WebForms 表單解析（successful controls 規則）
  http_trip_form.py  # 在記憶體中組出 POST payload（不送出）

scripts/             # 研究與診斷用 POC（多數為唯讀）
docs/                # 完整的調查與驗證記錄
tests/               # 103 個單元測試
```

## 測試

```powershell
python -m pytest tests/ -q
```

測試不需要連線到真實系統。

## 授權與免責

本工具針對特定 EIP 部署的實際行為開發，其他環境的畫面結構可能不同。使用前請自行確認，
並理解送件是無法復原的動作。
