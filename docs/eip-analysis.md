# EIP - 出差登記 網站探索分析報告

產出時間：2026-08-10 23:09:43 +0800

EIP URL：http://eip.example.com/EFNET/

## 1. 首頁結構

- 首頁標題：電子簽核
- 首頁 URL：http://eip.example.com/EFNET/
- Frame 數量：16
- **偵測到多個 frame（可能是傳統 frameset 或 iframe 結構）**

| # | name | url | is_main |
|---|---|---|---|
| 0 |  | http://eip.example.com/EFNET/ | True |
| 1 |  | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/TreeMainFrame.aspx | False |
| 2 | banner | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/titlebar1.aspx | False |
| 3 | contents1 | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/tree.aspx | False |
| 4 | marquee | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/Marquee.aspx | False |
| 5 | main | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/platform.aspx | False |
| 6 | chatFileFrame | about:blank | False |
| 7 | fileFrame | about:blank | False |
| 8 | framedefault | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/main.aspx | False |
| 9 | framehome | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/HomeTab.aspx | False |
| 10 | frameESSF21 | http://eip.example.com/EFNET/src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | False |
| 11 | framePlus | http://eip.example.com/HRMESS/src/ESS/ESSF21/ESSF21.aspx?Product=true&LoginId=E12345&TaskId=ESSF21&ClientIP=10.0.0.20&Identifier=0123456789abcdef0123456789abcdef&AFormType=FRM&AFormStatus=CREATE&ProductName=EFNET | False |
| 12 | ifrm-approveline | http://eip.example.com/EFNET/src/_Common/AppUtil/ApproveHistory/ApproveTimeline.aspx?FormId=&SheetNo= | False |
| 13 | iCover | about:blank | False |
| 14 | iSendDeptCover | about:blank | False |
| 15 | contents3 | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/ShowStatus.aspx | False |

## 2. 「出差登記」觸發元素

以文字關鍵字 `出差登記` 找到 6 個候選元素（依可能性排序，非唯一猜測 - 請人工確認正確項目）：

| tag | type | id | name | label（推測） | text | frame | 建議 selector |
|---|---|---|---|---|---|---|---|
| a |  | ESSF21 |  |  | 出差登記.. | c/_Common/AppUtil/FrameSet/platform.aspx | `#ESSF21` |
| td |  |  |  |  | 出差登記(E.. | /_Common/AppUtil/FrameSet/titlebar1.aspx | `td#tdMenu_1 > table > tbody > tr > td:nth-of-type(2)` |
| span |  | DscLabel27_lbl |  |  | 出差登記 | FRM&AFormStatus=CREATE&ProductName=EFNET | `#DscLabel27_lbl` |
| a |  | RESTreet8 |  |  | 出差登記 | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#RESTreet8` |
| font |  |  |  |  | 出差登記(ESSF21)(149) | T/src/_Common/AppUtil/FrameSet/tree.aspx | `div#treeUsedFunction > table > tbody > tr > td > a > font` |
| span |  | ESSCCDJ003_lbl |  |  | 出差登記ID | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ003_lbl` |

完整資訊（含 outerHTML / xpath）另存於 `config/selectors.discovered.json`。

## 3. 點擊後的行為

- 實際成功點擊的元素：tag=`a` id=`ESSF21` frame=`http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/platform.aspx`

- 偵測結果：**same_page_or_frame_unconfirmed**
  （沒有新視窗；同一個 Page 內以導覽或 frame 內容更新方式呈現）
- 表單頁 URL：http://eip.example.com/EFNET/
- 表單頁 Frame 數量：16

| # | name | url | is_main |
|---|---|---|---|
| 0 |  | http://eip.example.com/EFNET/ | True |
| 1 |  | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/TreeMainFrame.aspx | False |
| 2 | banner | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/titlebar1.aspx | False |
| 3 | contents1 | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/tree.aspx | False |
| 4 | marquee | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/Marquee.aspx | False |
| 5 | main | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/platform.aspx | False |
| 6 | chatFileFrame | about:blank | False |
| 7 | fileFrame | about:blank | False |
| 8 | framedefault | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/main.aspx | False |
| 9 | framehome | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/HomeTab.aspx | False |
| 10 | frameESSF21 | http://eip.example.com/EFNET/src/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | False |
| 11 | framePlus | http://eip.example.com/HRMESS/src/ESS/ESSF21/ESSF21.aspx?Product=true&LoginId=E12345&TaskId=ESSF21&ClientIP=10.0.0.20&Identifier=0123456789abcdef0123456789abcdef&AFormType=FRM&AFormStatus=CREATE&ProductName=EFNET | False |
| 12 | ifrm-approveline | http://eip.example.com/EFNET/src/_Common/AppUtil/ApproveHistory/ApproveTimeline.aspx?FormId=&SheetNo= | False |
| 13 | iCover | about:blank | False |
| 14 | iSendDeptCover | about:blank | False |
| 15 | contents3 | http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/ShowStatus.aspx | False |

## 4. 出差申請表單欄位清單

共找到 395 個 input / select / textarea / button 元素（跨所有 frame 遞迴掃描）：

| tag | type | id | name | label（推測） | text | frame | 建議 selector |
|---|---|---|---|---|---|---|---|
| input | hidden | __VIEWSTATE | __VIEWSTATE |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#__VIEWSTATE` |
| input | hidden | __VIEWSTATEGENERATOR | __VIEWSTATEGENERATOR |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#__VIEWSTATEGENERATOR` |
| input | hidden | __EVENTVALIDATION | __EVENTVALIDATION |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#__EVENTVALIDATION` |
| input | image | imgloginout_btn | imgloginout$btn | 出差登記(E..	 	 	補刷卡申請(..	 	 	考核指標 |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#imgloginout_btn` |
| input | image | imgfavorite_btn | imgfavorite$btn | 出差登記(E..	 	 	補刷卡申請(..	 	 	考核指標 |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#imgfavorite_btn` |
| input | image | imghome_btn | imghome$btn | 出差登記(E..	 	 	補刷卡申請(..	 	 	考核指標 |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#imghome_btn` |
| input | hidden | hidIsEnabledMetroUI | hidIsEnabledMetroUI | 出差登記(E..	 	 	補刷卡申請(..	 	 	考核指標 |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#hidIsEnabledMetroUI` |
| input | hidden | hiddenOpenTheSameTask | hiddenOpenTheSameTask |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#hiddenOpenTheSameTask` |
| input | hidden | hiddenIsRedirectToLoginPage | hiddenIsRedirectToLoginPage |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#hiddenIsRedirectToLoginPage` |
| input | hidden | hiddenIsDBLogin | hiddenIsDBLogin |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#hiddenIsDBLogin` |
| input | hidden | hidShowTimeOutPeriod | hidShowTimeOutPeriod |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#hidShowTimeOutPeriod` |
| input | hidden | hdnIsShowQRCodeScan | hdnIsShowQRCodeScan |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#hdnIsShowQRCodeScan` |
| input | hidden | hidLastWillTimeOutDateTime | hidLastWillTimeOutDateTime |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#hidLastWillTimeOutDateTime` |
| input | hidden | hidConfirmMsg | hidConfirmMsg |  |  | /_Common/AppUtil/FrameSet/titlebar1.aspx | `#hidConfirmMsg` |
| input | hidden | __EVENTTARGET | __EVENTTARGET |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#__EVENTTARGET` |
| input | hidden | __EVENTARGUMENT | __EVENTARGUMENT |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#__EVENTARGUMENT` |
| input | hidden | FormBoxTree_ExpandState | FormBoxTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#FormBoxTree_ExpandState` |
| input | hidden | FormBoxTree_SelectedNode | FormBoxTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#FormBoxTree_SelectedNode` |
| input | hidden | FormBoxTree_PopulateLog | FormBoxTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#FormBoxTree_PopulateLog` |
| input | hidden | RESTree_ExpandState | RESTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#RESTree_ExpandState` |
| input | hidden | RESTree_SelectedNode | RESTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#RESTree_SelectedNode` |
| input | hidden | RESTree_PopulateLog | RESTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#RESTree_PopulateLog` |
| input | hidden | ISOTree_ExpandState | ISOTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#ISOTree_ExpandState` |
| input | hidden | ISOTree_SelectedNode | ISOTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#ISOTree_SelectedNode` |
| input | hidden | ISOTree_PopulateLog | ISOTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#ISOTree_PopulateLog` |
| input | hidden | OATree_ExpandState | OATree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#OATree_ExpandState` |
| input | hidden | OATree_SelectedNode | OATree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#OATree_SelectedNode` |
| input | hidden | OATree_PopulateLog | OATree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#OATree_PopulateLog` |
| input | hidden | MTSTree_ExpandState | MTSTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#MTSTree_ExpandState` |
| input | hidden | MTSTree_SelectedNode | MTSTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#MTSTree_SelectedNode` |
| input | hidden | MTSTree_PopulateLog | MTSTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#MTSTree_PopulateLog` |
| input | hidden | HRESSTree_ExpandState | HRESSTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HRESSTree_ExpandState` |
| input | hidden | HRESSTree_SelectedNode | HRESSTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HRESSTree_SelectedNode` |
| input | hidden | HRESSTree_PopulateLog | HRESSTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HRESSTree_PopulateLog` |
| input | hidden | DMSTree_ExpandState | DMSTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#DMSTree_ExpandState` |
| input | hidden | DMSTree_SelectedNode | DMSTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#DMSTree_SelectedNode` |
| input | hidden | DMSTree_PopulateLog | DMSTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#DMSTree_PopulateLog` |
| input | hidden | treeAppFormESS_ExpandState | treeAppFormESS_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#treeAppFormESS_ExpandState` |
| input | hidden | treeAppFormESS_SelectedNode | treeAppFormESS_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#treeAppFormESS_SelectedNode` |
| input | hidden | treeAppFormESS_PopulateLog | treeAppFormESS_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#treeAppFormESS_PopulateLog` |
| input | hidden | treeAppFormEMS_ExpandState | treeAppFormEMS_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#treeAppFormEMS_ExpandState` |
| input | hidden | treeAppFormEMS_SelectedNode | treeAppFormEMS_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#treeAppFormEMS_SelectedNode` |
| input | hidden | treeAppFormEMS_PopulateLog | treeAppFormEMS_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#treeAppFormEMS_PopulateLog` |
| input | hidden | treeAppFormIAM_ExpandState | treeAppFormIAM_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#treeAppFormIAM_ExpandState` |
| input | hidden | treeAppFormIAM_SelectedNode | treeAppFormIAM_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#treeAppFormIAM_SelectedNode` |
| input | hidden | treeAppFormIAM_PopulateLog | treeAppFormIAM_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#treeAppFormIAM_PopulateLog` |
| input | hidden | NOATree_ExpandState | NOATree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#NOATree_ExpandState` |
| input | hidden | NOATree_SelectedNode | NOATree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#NOATree_SelectedNode` |
| input | hidden | NOATree_PopulateLog | NOATree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#NOATree_PopulateLog` |
| input | hidden | SP7Tree_ExpandState | SP7Tree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#SP7Tree_ExpandState` |
| input | hidden | SP7Tree_SelectedNode | SP7Tree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#SP7Tree_SelectedNode` |
| input | hidden | SP7Tree_PopulateLog | SP7Tree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#SP7Tree_PopulateLog` |
| input | hidden | MTMTree_ExpandState | MTMTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#MTMTree_ExpandState` |
| input | hidden | MTMTree_SelectedNode | MTMTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#MTMTree_SelectedNode` |
| input | hidden | MTMTree_PopulateLog | MTMTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#MTMTree_PopulateLog` |
| input | hidden | MDATree_ExpandState | MDATree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#MDATree_ExpandState` |
| input | hidden | MDATree_SelectedNode | MDATree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#MDATree_SelectedNode` |
| input | hidden | MDATree_PopulateLog | MDATree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#MDATree_PopulateLog` |
| input | hidden | PCMTree_ExpandState | PCMTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#PCMTree_ExpandState` |
| input | hidden | PCMTree_SelectedNode | PCMTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#PCMTree_SelectedNode` |
| input | hidden | PCMTree_PopulateLog | PCMTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#PCMTree_PopulateLog` |
| input | hidden | EETTree_ExpandState | EETTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EETTree_ExpandState` |
| input | hidden | EETTree_SelectedNode | EETTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EETTree_SelectedNode` |
| input | hidden | EETTree_PopulateLog | EETTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EETTree_PopulateLog` |
| input | hidden | DSSTree_ExpandState | DSSTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#DSSTree_ExpandState` |
| input | hidden | DSSTree_SelectedNode | DSSTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#DSSTree_SelectedNode` |
| input | hidden | DSSTree_PopulateLog | DSSTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#DSSTree_PopulateLog` |
| input | hidden | EBDTree_ExpandState | EBDTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBDTree_ExpandState` |
| input | hidden | EBDTree_SelectedNode | EBDTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBDTree_SelectedNode` |
| input | hidden | EBDTree_PopulateLog | EBDTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBDTree_PopulateLog` |
| input | hidden | EBETree_ExpandState | EBETree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBETree_ExpandState` |
| input | hidden | EBETree_SelectedNode | EBETree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBETree_SelectedNode` |
| input | hidden | EBETree_PopulateLog | EBETree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBETree_PopulateLog` |
| input | hidden | EBFTree_ExpandState | EBFTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBFTree_ExpandState` |
| input | hidden | EBFTree_SelectedNode | EBFTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBFTree_SelectedNode` |
| input | hidden | EBFTree_PopulateLog | EBFTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBFTree_PopulateLog` |
| input | hidden | EBGTree_ExpandState | EBGTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBGTree_ExpandState` |
| input | hidden | EBGTree_SelectedNode | EBGTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBGTree_SelectedNode` |
| input | hidden | EBGTree_PopulateLog | EBGTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBGTree_PopulateLog` |
| input | hidden | EBITree_ExpandState | EBITree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBITree_ExpandState` |
| input | hidden | EBITree_SelectedNode | EBITree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBITree_SelectedNode` |
| input | hidden | EBITree_PopulateLog | EBITree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#EBITree_PopulateLog` |
| input | hidden | RECTree_ExpandState | RECTree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#RECTree_ExpandState` |
| input | hidden | RECTree_SelectedNode | RECTree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#RECTree_SelectedNode` |
| input | hidden | RECTree_PopulateLog | RECTree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#RECTree_PopulateLog` |
| input | hidden | TFATree_ExpandState | TFATree_ExpandState |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#TFATree_ExpandState` |
| input | hidden | TFATree_SelectedNode | TFATree_SelectedNode |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#TFATree_SelectedNode` |
| input | hidden | TFATree_PopulateLog | TFATree_PopulateLog |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#TFATree_PopulateLog` |
| input | hidden | __MSPVSTATE | __MSPVSTATE |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#__MSPVSTATE` |
| input | hidden | __MSPVSTATE_ZIP | __MSPVSTATE_ZIP |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#__MSPVSTATE_ZIP` |
| input | hidden | __VIEWSTATE | __VIEWSTATE |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#__VIEWSTATE` |
| input | hidden | __EVENTVALIDATION | __EVENTVALIDATION |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#__EVENTVALIDATION` |
| input | button | btnLevel0 |  |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#btnLevel0` |
| input | button | btnLevel1 |  |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#btnLevel1` |
| input | button | btnLevel2 |  |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#btnLevel2` |
| input | image | UsedFunctionImageButton | UsedFunctionImageButton |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#UsedFunctionImageButton` |
| input | submit | refreshSYSComment | refreshSYSComment |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#refreshSYSComment` |
| input | hidden | HiddenField1 | HiddenField1 |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HiddenField1` |
| input | hidden | hiddenCurrentTabNum | hiddenCurrentTabNum |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#hiddenCurrentTabNum` |
| input | hidden | hiddenTimeoutMsg | hiddenTimeoutMsg |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#hiddenTimeoutMsg` |
| input | hidden | hiddenTimeoutRefreshSecond | hiddenTimeoutRefreshSecond |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#hiddenTimeoutRefreshSecond` |
| input | hidden | HiddenISO | HiddenISO |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HiddenISO` |
| input | hidden | HiddenOAS | HiddenOAS |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HiddenOAS` |
| input | hidden | HiddenMTS | HiddenMTS |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HiddenMTS` |
| input | hidden | HiddenESS | HiddenESS |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HiddenESS` |
| input | hidden | HiddenDMS | HiddenDMS |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HiddenDMS` |
| input | hidden | HiddenNOA | HiddenNOA |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HiddenNOA` |
| input | hidden | HiddenMTM | HiddenMTM |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#HiddenMTM` |
| input | submit | hiddenRefreshFormBoxNum | hiddenRefreshFormBoxNum |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#hiddenRefreshFormBoxNum` |
| input | hidden | hiddenIsOnloadReady | hiddenIsOnloadReady |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#hiddenIsOnloadReady` |
| input | hidden | hidConfirmMsg | hidConfirmMsg |  |  | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#hidConfirmMsg` |
| select |  | ddlModule | ddlModule |  | 請選擇.. RES電子表單模組 ESS PLUS模組 移動社 | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#ddlModule` |
| input | hidden | __VIEWSTATE | __VIEWSTATE |  |  | rc/_Common/AppUtil/FrameSet/Marquee.aspx | `#__VIEWSTATE` |
| input | hidden | __VIEWSTATEGENERATOR | __VIEWSTATEGENERATOR |  |  | rc/_Common/AppUtil/FrameSet/Marquee.aspx | `#__VIEWSTATEGENERATOR` |
| input | hidden | __VIEWSTATE | __VIEWSTATE |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#__VIEWSTATE` |
| input | hidden | __VIEWSTATEGENERATOR | __VIEWSTATEGENERATOR |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#__VIEWSTATEGENERATOR` |
| input | hidden | __EVENTVALIDATION | __EVENTVALIDATION |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#__EVENTVALIDATION` |
| input | button | btCreatjQTab |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#btCreatjQTab` |
| input | button | btClosejQTab |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#btClosejQTab` |
| input | button | btReSetjQTabInfo |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#btReSetjQTabInfo` |
| input | hidden | hdLocation |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdLocation` |
| input | hidden | hdId |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdId` |
| input | hidden | hdText |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdText` |
| input | hidden | hdTextWidth |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdTextWidth` |
| input | hidden | hdCloseTabId |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdCloseTabId` |
| input | hidden | hdTabSelectIndex |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdTabSelectIndex` |
| input | hidden | hdTabFormId |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdTabFormId` |
| input | hidden | hdTabFormName |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdTabFormName` |
| input | hidden | hdUrl |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdUrl` |
| input | hidden | currentTabId |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#currentTabId` |
| input | hidden | currentTabIndex |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#currentTabIndex` |
| input | hidden | startTab |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#startTab` |
| input | hidden | tabNavAlign |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#tabNavAlign` |
| input | hidden | hiddenOpenTheSameTask | hiddenOpenTheSameTask |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hiddenOpenTheSameTask` |
| input | hidden | hiddenMaxDisplayTabNum | hiddenMaxDisplayTabNum |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hiddenMaxDisplayTabNum` |
| input | hidden | HDF_tabSelectIndex | HDF_tabSelectIndex |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#HDF_tabSelectIndex` |
| input | hidden | createTabIdName | createTabIdName |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#createTabIdName` |
| input | hidden | indexPageToolHeight | indexPageToolHeight |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#indexPageToolHeight` |
| input | hidden | hiddenIsOnloadReady | hiddenIsOnloadReady |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hiddenIsOnloadReady` |
| input | hidden | hiddenMenuWidth | hiddenMenuWidth |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hiddenMenuWidth` |
| input | hidden | hidIsEnabledMetroUI | hidIsEnabledMetroUI |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hidIsEnabledMetroUI` |
| input | hidden | hidIsEnabledSysAlert | hidIsEnabledSysAlert |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hidIsEnabledSysAlert` |
| input | hidden | hidConfirmMsg | hidConfirmMsg |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hidConfirmMsg` |
| input | hidden | hdnIsShowNodeMsg | hdnIsShowNodeMsg |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdnIsShowNodeMsg` |
| input | hidden | hdnChatFileAction | hdnChatFileAction |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#hdnChatFileAction` |
| button |  | chatFileBtn |  |  |  | c/_Common/AppUtil/FrameSet/platform.aspx | `#chatFileBtn` |
| button |  | arrowBtn |  |  | > | c/_Common/AppUtil/FrameSet/platform.aspx | `#arrowBtn` |
| input | hidden | __VIEWSTATE | __VIEWSTATE |  |  | T/src/_Common/AppUtil/FrameSet/main.aspx | `#__VIEWSTATE` |
| input | hidden | __VIEWSTATEGENERATOR | __VIEWSTATEGENERATOR |  |  | T/src/_Common/AppUtil/FrameSet/main.aspx | `#__VIEWSTATEGENERATOR` |
| input | hidden | __VIEWSTATE | __VIEWSTATE |  |  | rc/_Common/AppUtil/FrameSet/HomeTab.aspx | `#__VIEWSTATE` |
| input | hidden | __VIEWSTATEGENERATOR | __VIEWSTATEGENERATOR |  |  | rc/_Common/AppUtil/FrameSet/HomeTab.aspx | `#__VIEWSTATEGENERATOR` |
| input | hidden | __EVENTTARGET | __EVENTTARGET |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#__EVENTTARGET` |
| input | hidden | __EVENTARGUMENT | __EVENTARGUMENT |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#__EVENTARGUMENT` |
| input | hidden | __MSPVSTATE | __MSPVSTATE |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#__MSPVSTATE` |
| input | hidden | __MSPVSTATE_ZIP | __MSPVSTATE_ZIP |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#__MSPVSTATE_ZIP` |
| input | hidden | __VIEWSTATE | __VIEWSTATE |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#__VIEWSTATE` |
| input | hidden | __EVENTVALIDATION | __EVENTVALIDATION |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#__EVENTVALIDATION` |
| input | image | MasterPage_btnPreCreateToolSendForm | MasterPage$btnPreCreateToolSendForm |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btnPreCreateToolSendForm` |
| input | image | MasterPage_btnCreateToolSendForm | MasterPage$btnCreateToolSendForm |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btnCreateToolSendForm` |
| input | image | MasterPage_btnCreateToolSaveForm | MasterPage$btnCreateToolSaveForm |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btnCreateToolSaveForm` |
| input | image | MasterPage_btnPreCreateToolRefresh | MasterPage$btnPreCreateToolRefresh |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btnPreCreateToolRefresh` |
| input | image | MasterPage_btnCreateToolRefresh | MasterPage$btnCreateToolRefresh |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btnCreateToolRefresh` |
| input | image | MasterPage_btnPreCreateToolSimulation | MasterPage$btnPreCreateToolSimulation |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btnPreCreateToolSimulation` |
| input | image | MasterPage_btnCreateToolSimulation | MasterPage$btnCreateToolSimulation |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btnCreateToolSimulation` |
| input | text | MasterPage_txtCreateToolFormID_txt | MasterPage$txtCreateToolFormID$txt | 單別： |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_txtCreateToolFormID_txt` |
| input | text | MasterPage_txtCreateToolSheetNo_txt | MasterPage$txtCreateToolSheetNo$txt | 單號： |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_txtCreateToolSheetNo_txt` |
| input | text | MasterPage_txtCreateToolSubject_txt2hdn | MasterPage$txtCreateToolSubject$txt2hdn |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_txtCreateToolSubject_txt2hdn` |
| input | radio | MasterPage_rblCreateToolImportant_0 | MasterPage$rblCreateToolImportant | 低 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_rblCreateToolImportant_0` |
| input | radio | MasterPage_rblCreateToolImportant_1 | MasterPage$rblCreateToolImportant | 普通 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_rblCreateToolImportant_1` |
| input | radio | MasterPage_rblCreateToolImportant_2 | MasterPage$rblCreateToolImportant | 高 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_rblCreateToolImportant_2` |
| input | hidden | MasterPage_hdnNewUploadFiles | MasterPage$hdnNewUploadFiles |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdnNewUploadFiles` |
| input | hidden | MasterPage_hdnWEISimUIInfo | MasterPage$hdnWEISimUIInfo |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdnWEISimUIInfo` |
| input | text | MasterPage_MasterPageContent_epiess003_txt | MasterPage$MasterPageContent$epiess003$txt | FD-EPIE001-epiess003 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_epiess003_txt` |
| input | text | MasterPage_MasterPageContent_epiess005_txt | MasterPage$MasterPageContent$epiess005$txt | FD-EPIE001-epiess005 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_epiess005_txt` |
| input | text | MasterPage_MasterPageContent_epiess006_txt | MasterPage$MasterPageContent$epiess006$txt | FD-EPIE001-epiess008 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_epiess006_txt` |
| input | text | MasterPage_MasterPageContent_epiess007_txt | MasterPage$MasterPageContent$epiess007$txt | FD-EPIE001-epiess009 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_epiess007_txt` |
| input | text | MasterPage_MasterPageContent_epiess008_txt | MasterPage$MasterPageContent$epiess008$txt | FD-EPIE001-epiess010 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_epiess008_txt` |
| input | text | MasterPage_MasterPageContent_epiess009_txt | MasterPage$MasterPageContent$epiess009$txt | FD-EPIE001-epiess011 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_epiess009_txt` |
| input | text | MasterPage_MasterPageContent_epiess001_txt | MasterPage$MasterPageContent$epiess001$txt | FD-EPIE001-epiess001 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_epiess001_txt` |
| input | text | MasterPage_MasterPageContent_epiess002_txt | MasterPage$MasterPageContent$epiess002$txt | FD-EPIE001-epiess002 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_epiess002_txt` |
| input | hidden | MasterPage_MasterPageContent_currentDiv | MasterPage$MasterPageContent$currentDiv |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_currentDiv` |
| input | hidden | MasterPage_MasterPageContent_hasToDeleteLastNewRow | MasterPage$MasterPageContent$hasToDeleteLastNewRow |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_hasToDeleteLastNewRow` |
| input | hidden | MasterPage_MasterPageContent_startTab1 | MasterPage$MasterPageContent$startTab1 |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_startTab1` |
| input | hidden | MasterPage_MasterPageContent_currentTabId1 | MasterPage$MasterPageContent$currentTabId1 |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_currentTabId1` |
| input | hidden | MasterPage_MasterPageContent_currentTabIndex1 | MasterPage$MasterPageContent$currentTabIndex1 |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_currentTabIndex1` |
| input | hidden | MasterPage_MasterPageContent_startTab2 | MasterPage$MasterPageContent$startTab2 |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_startTab2` |
| input | hidden | MasterPage_MasterPageContent_currentTabId2 | MasterPage$MasterPageContent$currentTabId2 |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_currentTabId2` |
| input | hidden | MasterPage_MasterPageContent_currentTabIndex2 | MasterPage$MasterPageContent$currentTabIndex2 |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_currentTabIndex2` |
| input | hidden | MasterPage_MasterPageContent_startTab3 | MasterPage$MasterPageContent$startTab3 |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_startTab3` |
| input | hidden | MasterPage_MasterPageContent_currentTabId3 | MasterPage$MasterPageContent$currentTabId3 |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_currentTabId3` |
| input | hidden | MasterPage_MasterPageContent_currentTabIndex3 | MasterPage$MasterPageContent$currentTabIndex3 |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_currentTabIndex3` |
| input | hidden | MasterPage_MasterPageContent_hdnUniqueTaskId | MasterPage$MasterPageContent$hdnUniqueTaskId |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_hdnUniqueTaskId` |
| input | hidden | MasterPage_MasterPageContent_I18NLanguageType | MasterPage$MasterPageContent$I18NLanguageType |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_I18NLanguageType` |
| input | hidden | MasterPage_MasterPageContent_hdnESSProgsHeightSelf | MasterPage$MasterPageContent$hdnESSProgsHeightSelf |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_hdnESSProgsHeightSelf` |
| input | hidden | MasterPage_MasterPageContent_hdnplusFrameUrl | MasterPage$MasterPageContent$hdnplusFrameUrl |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_hdnplusFrameUrl` |
| input | hidden | MasterPage_MasterPageContent_hdnShowDivInit | MasterPage$MasterPageContent$hdnShowDivInit |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_hdnShowDivInit` |
| input | hidden | MasterPage_hdnCheckBypass | MasterPage$hdnCheckBypass |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdnCheckBypass` |
| input | hidden | MasterPage_hdWithDrawReason | MasterPage$hdWithDrawReason |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdWithDrawReason` |
| input | button | MasterPage_btWithDrawOK | MasterPage$btWithDrawOK |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btWithDrawOK` |
| input | button | MasterPage_btWithDrawNo | MasterPage$btWithDrawNo |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btWithDrawNo` |
| input | image | MasterPage_hdBTWithDrawOK | MasterPage$hdBTWithDrawOK |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdBTWithDrawOK` |
| input | hidden | MasterPage_hdSendDeptValue | MasterPage$hdSendDeptValue |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdSendDeptValue` |
| input | hidden | MasterPage_hdInvokeType | MasterPage$hdInvokeType |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdInvokeType` |
| input | button | MasterPage_btSendDeptOK | MasterPage$btSendDeptOK |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btSendDeptOK` |
| input | button | MasterPage_btSendDeptNo | MasterPage$btSendDeptNo |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_btSendDeptNo` |
| input | hidden | MasterPage_hdParserRoleId | MasterPage$hdParserRoleId |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdParserRoleId` |
| input | hidden | MasterPage_hdIsRefresh | MasterPage$hdIsRefresh |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdIsRefresh` |
| input | hidden | MasterPage_hdIsShowFlowByApp | MasterPage$hdIsShowFlowByApp |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdIsShowFlowByApp` |
| input | hidden | MasterPage_hdApproveType | MasterPage$hdApproveType |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdApproveType` |
| input | hidden | MasterPage_hdApproveTypeForward | MasterPage$hdApproveTypeForward |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdApproveTypeForward` |
| input | hidden | MasterPage_hdBorwserPrintInfo | MasterPage$hdBorwserPrintInfo |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdBorwserPrintInfo` |
| input | hidden | hdIsShow |  |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#hdIsShow` |
| input | hidden | MasterPage_hdYiFeiField | MasterPage$hdYiFeiField |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdYiFeiField` |
| input | hidden | MasterPage_hdChangeHead | MasterPage$hdChangeHead |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdChangeHead` |
| input | hidden | MasterPage_hdChangeBody | MasterPage$hdChangeBody |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdChangeBody` |
| input | hidden | MasterPage_hdBodySum | MasterPage$hdBodySum |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_hdBodySum` |
| input | hidden | MasterPage_universalID | MasterPage$universalID |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_universalID` |
| input | hidden | PLUSIdentity | PLUSIdentity |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#PLUSIdentity` |
| textarea |  | MasterPage_txtCreateToolSubject_txt | MasterPage$txtCreateToolSubject$txt | 主旨： |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_txtCreateToolSubject_txt` |
| textarea |  | MasterPage_MasterPageContent_epiess004_txt | MasterPage$MasterPageContent$epiess004$txt | FD-EPIE001-epiess004 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_MasterPageContent_epiess004_txt` |
| textarea |  | MasterPage_txbWithDrawReason_txt | MasterPage$txbWithDrawReason$txt |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_txbWithDrawReason_txt` |
| button | button | cboxPrevious |  |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#cboxPrevious` |
| button | button | cboxNext |  |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#cboxNext` |
| button |  | cboxSlideshow |  |  |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#cboxSlideshow` |
| input | hidden | __EVENTTARGET | __EVENTTARGET |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#__EVENTTARGET` |
| input | hidden | __EVENTARGUMENT | __EVENTARGUMENT |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#__EVENTARGUMENT` |
| input | hidden | __TabStrip2_State__ | __TabStrip2_State__ |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#__TabStrip2_State__` |
| input | hidden | __MSPVSTATE | __MSPVSTATE |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#__MSPVSTATE` |
| input | hidden | __MSPVSTATE_ZIP | __MSPVSTATE_ZIP |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#__MSPVSTATE_ZIP` |
| input | image | BtnDetailSave | BtnDetailSave |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnDetailSave` |
| input | image | BtnDetailAdd | BtnDetailAdd |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnDetailAdd` |
| input | image | BtnDetailDel | BtnDetailDel |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnDetailDel` |
| input | image | BtnDetailExit | BtnDetailExit |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnDetailExit` |
| input | image | BtnToSelectSingleDetail | BtnToSelectSingleDetail |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnToSelectSingleDetail` |
| input | image | BtnAdd | BtnAdd |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnAdd` |
| input | image | BtnImgAdd_btn | BtnImgAdd$btn |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnImgAdd_btn` |
| input | image | BtnSave | BtnSave |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnSave` |
| input | image | BtnImgSave_btn | BtnImgSave$btn |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnImgSave_btn` |
| input | image | BtnSave2 | BtnSave2 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnSave2` |
| input | image | BtnImgSave2_btn | BtnImgSave2$btn |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnImgSave2_btn` |
| input | image | BtnExit | BtnExit |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnExit` |
| input | image | BtnImgExit_btn | BtnImgExit$btn |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnImgExit_btn` |
| input | image | BtnPreRecord | BtnPreRecord |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnPreRecord` |
| input | image | BtnBackToHeadGrid | BtnBackToHeadGrid |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnBackToHeadGrid` |
| input | image | BtnNextRecord | BtnNextRecord |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnNextRecord` |
| input | image | BtnImgPreRecord_btn | BtnImgPreRecord$btn |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnImgPreRecord_btn` |
| input | image | BtnImgBackToHeadGrid_btn | BtnImgBackToHeadGrid$btn |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnImgBackToHeadGrid_btn` |
| input | image | BtnImgNextRecord_btn | BtnImgNextRecord$btn |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnImgNextRecord_btn` |
| input | image | BtnToLoadBody1 | BtnToLoadBody1 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnToLoadBody1` |
| input | image | BtnTempSave | BtnTempSave |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnTempSave` |
| input | image | BtnFlowBrowser | BtnFlowBrowser |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnFlowBrowser` |
| input | image | BtnFlow | BtnFlow |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnFlow` |
| input | image | BtnCreateSaveTempSave | BtnCreateSaveTempSave |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnCreateSaveTempSave` |
| input | image | BtnApproveSaveTempSave | BtnApproveSaveTempSave |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#BtnApproveSaveTempSave` |
| input | text | ESSCCDJ004_txt | ESSCCDJ004$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ004_txt` |
| input | text | ESSCCDJ005_txt | ESSCCDJ005$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ005_txt` |
| input | text | ESSCCDJ006_txt | ESSCCDJ006$txt | 填單人公司ID |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ006_txt` |
| input | text | ESSCCDJ007_txt | ESSCCDJ007$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ007_txt` |
| input | text | ESSCCDJ008_txt | ESSCCDJ008$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ008_txt` |
| input | text | ESSCCDJ009_txt | ESSCCDJ009$txt | 填單人部門ID |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ009_txt` |
| input | text | ESSCCDJ010_txt | ESSCCDJ010$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ010_txt` |
| input | text | ESSCCDJ011_txt | ESSCCDJ011$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ011_txt` |
| input | text | ESSCCDJ012_txt | ESSCCDJ012$txt | 填單人職位ID |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ012_txt` |
| input | text | ESSCCDJ013_txt | ESSCCDJ013$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ013_txt` |
| input | text | ESSCCDJ014_txt | ESSCCDJ014$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ014_txt` |
| input | text | ESSCCDJ015_txt | ESSCCDJ015$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ015_txt` |
| input | text | ESSCCDJ033_txt | ESSCCDJ033$txt | 申請人ID |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ033_txt` |
| input | text | ESSCCDJ039_txt | ESSCCDJ039$txt | 公司部門 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ039_txt` |
| input | text | ESSCCDJ034_txt | ESSCCDJ034$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ034_txt` |
| input | text | ESSCCDJ035_txt | ESSCCDJ035$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ035_txt` |
| input | radio | ESSCCDJ016_rdbl_0 | ESSCCDJ016$rdbl | 按申請登記 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ016_rdbl_0` |
| input | radio | ESSCCDJ016_rdbl_1 | ESSCCDJ016$rdbl | 直接登記 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ016_rdbl_1` |
| input | text | ESSCCDJ018_txt | ESSCCDJ018$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ018_txt` |
| input | text | hidRetValue | hidRetValue |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hidRetValue` |
| input | text | ESSCCDJ017_txt | ESSCCDJ017$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ017_txt` |
| input | text | ESSCCDJ019_txt | ESSCCDJ019$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ019_txt` |
| input | text | ESSCCDJ020_txt | ESSCCDJ020$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ020_txt` |
| input | text | ESSCCDJ021_txt | ESSCCDJ021$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ021_txt` |
| input | text | ESSCCDJ022_txt | ESSCCDJ022$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ022_txt` |
| input | checkbox | ESSCCDJ023_chk | ESSCCDJ023$chk |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ023_chk` |
| input | hidden | ESSCCDJ023_hid | ESSCCDJ023_hid |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ023_hid` |
| input | checkbox | ESSCCDJ023_1_chk | ESSCCDJ023_1$chk |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ023_1_chk` |
| input | hidden | ESSCCDJ023_1_hid | ESSCCDJ023_1_hid |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ023_1_hid` |
| input | checkbox | ESSCCDJ038_chk | ESSCCDJ038$chk |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ038_chk` |
| input | hidden | ESSCCDJ038_hid | ESSCCDJ038_hid |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ038_hid` |
| input | text | ESSCCDJ024_txt | ESSCCDJ024$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ024_txt` |
| input | text | ESSCCDJ025_txt | ESSCCDJ025$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ025_txt` |
| input | text | ESSCCDJ026_txt | ESSCCDJ026$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ026_txt` |
| input | text | ESSCCDJ027_txt | ESSCCDJ027$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ027_txt` |
| input | text | ESSCCDJ001_txt | ESSCCDJ001$txt | 單別 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ001_txt` |
| input | text | ESSCCDJ002_txt | ESSCCDJ002$txt | 單號 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ002_txt` |
| input | text | ESSCCDJ003_txt | ESSCCDJ003$txt | 出差登記ID |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ003_txt` |
| input | text | ESSCCDJ030_txt | ESSCCDJ030$txt | 直接主管ID |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ030_txt` |
| input | text | ESSCCDJ031_txt | ESSCCDJ031$txt | 直接主管Code |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ031_txt` |
| input | text | ESSCCDJ032_txt | ESSCCDJ032$txt | 直接主管姓名 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ032_txt` |
| input | text | ESSCCDD001_txt | ESSCCDD001$txt | 單別 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD001_txt` |
| input | text | ESSCCDD002_txt | ESSCCDD002$txt | 單號 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD002_txt` |
| input | text | ESSCCDD003_txt | ESSCCDD003$txt | 序號 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD003_txt` |
| input | text | ESSCCDD004_txt | ESSCCDD004$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD004_txt` |
| input | text | ESSCCDD005_txt | ESSCCDD005$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD005_txt` |
| input | text | ESSCCDD006_txt | ESSCCDD006$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD006_txt` |
| input | text | ESSCCDD007_txt | ESSCCDD007$txt | 出差人公司ID |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD007_txt` |
| input | text | ESSCCDD008_txt | ESSCCDD008$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD008_txt` |
| input | text | ESSCCDD009_txt | ESSCCDD009$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD009_txt` |
| input | text | ESSCCDD010_txt | ESSCCDD010$txt | 出差人部門ID |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD010_txt` |
| input | text | ESSCCDD011_txt | ESSCCDD011$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD011_txt` |
| input | text | ESSCCDD012_txt | ESSCCDD012$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD012_txt` |
| input | text | ESSCCDD013_txt | ESSCCDD013$txt | 出差人職位ID |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD013_txt` |
| input | text | ESSCCDD014_txt | ESSCCDD014$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD014_txt` |
| input | text | ESSCCDD015_txt | ESSCCDD015$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD015_txt` |
| input | text | ESSCCDD016_txt | ESSCCDD016$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDD016_txt` |
| input | submit | GridUserControl1_BtnExtraField | GridUserControl1$BtnExtraField |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_BtnExtraField` |
| input | submit | GridUserControl1_Button6 | GridUserControl1$Button6 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_Button6` |
| input | submit | GridUserControl1_Button7 | GridUserControl1$Button7 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_Button7` |
| input | submit | GridUserControl1_Button9 | GridUserControl1$Button9 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_Button9` |
| input | submit | GridUserControl1_Button10 | GridUserControl1$Button10 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_Button10` |
| input | submit | GridUserControl1_BtnToDesign | GridUserControl1$BtnToDesign |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_BtnToDesign` |
| input | submit | GridUserControl1_BtnToExcel | GridUserControl1$BtnToExcel |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_BtnToExcel` |
| input | hidden | GridUserControl1_rowIndex_detail | GridUserControl1$rowIndex_detail |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_rowIndex_detail` |
| input | hidden | GridUserControl1_hdnGS001 | GridUserControl1$hdnGS001 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnGS001` |
| input | hidden | GridUserControl1_header | GridUserControl1$header |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_header` |
| input | hidden | GridUserControl1_tempDefaultValueDetail | GridUserControl1$tempDefaultValueDetail |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_tempDefaultValueDetail` |
| input | hidden | GridUserControl1_hdnCheckedIndex | GridUserControl1$hdnCheckedIndex |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnCheckedIndex` |
| input | hidden | GridUserControl1_hdnBtnSaveEnabled | GridUserControl1$hdnBtnSaveEnabled |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnBtnSaveEnabled` |
| input | hidden | GridUserControl1_hdnGS002 | GridUserControl1$hdnGS002 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnGS002` |
| input | hidden | GridUserControl1_hdnShowColumn | GridUserControl1$hdnShowColumn |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnShowColumn` |
| input | hidden | GridUserControl1_hdnPageNo | GridUserControl1$hdnPageNo |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnPageNo` |
| input | hidden | GridUserControl1_rowIndex_predetail | GridUserControl1$rowIndex_predetail |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_rowIndex_predetail` |
| input | hidden | GridUserControl1_Hidden1 | GridUserControl1$Hidden1 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_Hidden1` |
| input | hidden | GridUserControl1_hdnTabIndex | GridUserControl1$hdnTabIndex |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnTabIndex` |
| input | hidden | GridUserControl1_hdnStatus | GridUserControl1$hdnStatus |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnStatus` |
| input | hidden | GridUserControl1_hdnNowIsNew | GridUserControl1$hdnNowIsNew |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnNowIsNew` |
| input | hidden | GridUserControl1_hdnEditingRow | GridUserControl1$hdnEditingRow |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnEditingRow` |
| input | hidden | GridUserControl1_hdnIsEditPressed | GridUserControl1$hdnIsEditPressed |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnIsEditPressed` |
| input | hidden | GridUserControl1_hdnMgtStatus | GridUserControl1$hdnMgtStatus |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnMgtStatus` |
| input | hidden | GridUserControl1_hdnSYSConfig_EnableCancelEdit | GridUserControl1$hdnSYSConfig_EnableCancelEdit |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnSYSConfig_EnableCancelEdit` |
| input | hidden | GridUserControl1_hdnQueryMode | GridUserControl1$hdnQueryMode |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#GridUserControl1_hdnQueryMode` |
| input | hidden | currentDiv | currentDiv |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#currentDiv` |
| input | hidden | headIndex | headIndex |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#headIndex` |
| input | hidden | headKeyValue | headKeyValue |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#headKeyValue` |
| input | hidden | qbeWhere | qbeWhere |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#qbeWhere` |
| input | hidden | ToolBarInfo | ToolBarInfo |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ToolBarInfo` |
| input | hidden | headIndexForLightBar | headIndexForLightBar |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#headIndexForLightBar` |
| input | hidden | hasToDeleteLastNewRow | hasToDeleteLastNewRow |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hasToDeleteLastNewRow` |
| input | hidden | hdnConfirm | hdnConfirm |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hdnConfirm` |
| input | hidden | deleteList | deleteList |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#deleteList` |
| input | hidden | NowGridControlName | NowGridControlName |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#NowGridControlName` |
| input | hidden | hdnHeadPageSize | hdnHeadPageSize |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hdnHeadPageSize` |
| input | hidden | startTab1 | startTab1 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#startTab1` |
| input | hidden | currentTabId1 | currentTabId1 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#currentTabId1` |
| input | hidden | currentTabIndex1 | currentTabIndex1 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#currentTabIndex1` |
| input | hidden | startTab2 | startTab2 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#startTab2` |
| input | hidden | currentTabId2 | currentTabId2 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#currentTabId2` |
| input | hidden | currentTabIndex2 | currentTabIndex2 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#currentTabIndex2` |
| input | hidden | startTab3 | startTab3 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#startTab3` |
| input | hidden | currentTabId3 | currentTabId3 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#currentTabId3` |
| input | hidden | currentTabIndex3 | currentTabIndex3 |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#currentTabIndex3` |
| input | hidden | hdnUniqueTaskId | hdnUniqueTaskId |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hdnUniqueTaskId` |
| input | hidden | I18NLanguageType | I18NLanguageType |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#I18NLanguageType` |
| input | hidden | hdnMonitorFlag | hdnMonitorFlag |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hdnMonitorFlag` |
| input | hidden | ProductUrl | ProductUrl |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ProductUrl` |
| input | hidden | ProductAction | ProductAction |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ProductAction` |
| input | hidden | ProductIdentifier | ProductIdentifier |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ProductIdentifier` |
| input | hidden | ProductUniversalID | ProductUniversalID |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ProductUniversalID` |
| input | hidden | ProductFormID | ProductFormID |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ProductFormID` |
| input | hidden | ProductParameters | ProductParameters |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ProductParameters` |
| input | hidden | hdnGridData | hdnGridData |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hdnGridData` |
| input | hidden | hdnGridDataCount | hdnGridDataCount |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hdnGridDataCount` |
| input | hidden | hdnHasGridNewRow | hdnHasGridNewRow |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hdnHasGridNewRow` |
| input | hidden | hdnRefreshGrid | hdnRefreshGrid |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#hdnRefreshGrid` |
| input | hidden | TriggerID | TriggerID |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#TriggerID` |
| input | hidden | universalID | universalID |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#universalID` |
| textarea |  | ESSCCDJ028_txt | ESSCCDJ028$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ028_txt` |
| textarea |  | ESSCCDJ037_txt | ESSCCDJ037$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ037_txt` |
| textarea |  | ESSCCDJ029_txt | ESSCCDJ029$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ029_txt` |
| textarea |  | ESSCCDJ036_txt | ESSCCDJ036$txt |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ036_txt` |
| input | hidden | __MSPVSTATE | __MSPVSTATE |  |  | ry/ApproveTimeline.aspx?FormId=&SheetNo= | `#__MSPVSTATE` |
| input | hidden | __MSPVSTATE_ZIP | __MSPVSTATE_ZIP |  |  | ry/ApproveTimeline.aspx?FormId=&SheetNo= | `#__MSPVSTATE_ZIP` |
| input | hidden | __VIEWSTATE | __VIEWSTATE |  |  | ry/ApproveTimeline.aspx?FormId=&SheetNo= | `#__VIEWSTATE` |
| input | hidden | __EVENTTARGET | __EVENTTARGET |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#__EVENTTARGET` |
| input | hidden | __EVENTARGUMENT | __EVENTARGUMENT |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#__EVENTARGUMENT` |
| input | hidden | __LASTFOCUS | __LASTFOCUS |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#__LASTFOCUS` |
| input | hidden | __VIEWSTATE | __VIEWSTATE |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#__VIEWSTATE` |
| input | hidden | __VIEWSTATEGENERATOR | __VIEWSTATEGENERATOR |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#__VIEWSTATEGENERATOR` |
| input | hidden | __EVENTVALIDATION | __EVENTVALIDATION |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#__EVENTVALIDATION` |
| input | text | hiddenOpenRight | hiddenOpenRight |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#hiddenOpenRight` |
| input | text | hiddenOpenTop | hiddenOpenTop |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#hiddenOpenTop` |
| input | hidden | hiddenIsOrNotOpenLeft | hiddenIsOrNotOpenLeft |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#hiddenIsOrNotOpenLeft` |
| input | hidden | hiddenIsOrNotOpenDown | hiddenIsOrNotOpenDown |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#hiddenIsOrNotOpenDown` |
| input | hidden | hiddenIsOrNotUserHome | hiddenIsOrNotUserHome |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#hiddenIsOrNotUserHome` |
| input | hidden | hiddenIsOrNotUseDesktop | hiddenIsOrNotUseDesktop |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#hiddenIsOrNotUseDesktop` |
| input | hidden | hiddenIsOrNotEFHome | hiddenIsOrNotEFHome |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#hiddenIsOrNotEFHome` |
| input | hidden | hdLangChangeTest | hdLangChangeTest |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#hdLangChangeTest` |
| input | hidden | hiddenIsOnloadReady | hiddenIsOnloadReady |  |  | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#hiddenIsOnloadReady` |
| select |  | DropDownList1 | DropDownList1 | 語系 | 繁體中文 簡體中文 | _Common/AppUtil/FrameSet/ShowStatus.aspx | `#DropDownList1` |

### Checkbox（共 3）

| tag | type | id | name | label（推測） | text | frame | 建議 selector |
|---|---|---|---|---|---|---|---|
| input | checkbox | ESSCCDJ023_chk | ESSCCDJ023$chk |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ023_chk` |
| input | checkbox | ESSCCDJ023_1_chk | ESSCCDJ023_1$chk |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ023_1_chk` |
| input | checkbox | ESSCCDJ038_chk | ESSCCDJ038$chk |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ038_chk` |

### Radio（共 5）

| tag | type | id | name | label（推測） | text | frame | 建議 selector |
|---|---|---|---|---|---|---|---|
| input | radio | MasterPage_rblCreateToolImportant_0 | MasterPage$rblCreateToolImportant | 低 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_rblCreateToolImportant_0` |
| input | radio | MasterPage_rblCreateToolImportant_1 | MasterPage$rblCreateToolImportant | 普通 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_rblCreateToolImportant_1` |
| input | radio | MasterPage_rblCreateToolImportant_2 | MasterPage$rblCreateToolImportant | 高 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_rblCreateToolImportant_2` |
| input | radio | ESSCCDJ016_rdbl_0 | ESSCCDJ016$rdbl | 按申請登記 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ016_rdbl_0` |
| input | radio | ESSCCDJ016_rdbl_1 | ESSCCDJ016$rdbl | 直接登記 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ016_rdbl_1` |

### Select 選項內容

- `ddlModule`：請選擇..(0), RES電子表單模組(RES), ESS PLUS模組(AppFormESS), 移動社交辦公(IMG)
- `DropDownList1`：繁體中文(Lang01), 簡體中文(Lang03)

## 5. 截圖清單

- `screenshots/01_home_after_attach.png`
- `screenshots/02_before_click_trip_registration.png`
- `screenshots/03_trip_form_page.png`
- `screenshots/04_form_fields_body.png` — 出差申請/出差類別/日期時間/出差地點/出差原因/備註（人工捲動後截圖）
- `screenshots/05_form_detail_grid.png` — 表單最下方的「出差明細」出差人清單（目前是空的）

## 6. Session 保存

- 此次分析是連線到你手動啟動並登入的 Edge (CDP attach)，並非由本程式建立/儲存的 session 檔案。
- EIP 要求 Windows 整合驗證（NTLM/Negotiate），Playwright 自行啟動的瀏覽器無法完成這個驗證且不會顯示原生登入框，因此改用「連線到你手動啟動並登入的 Edge」（Chrome DevTools Protocol attach）方式，而非 Playwright 產生/保存的 storage_state 檔案。
- Edge 使用獨立的 profile 目錄 `C:\Users\youruser\OneDrive - example.com\桌面\個人\EIP自動化\eip-trip-assistant\.edge-profile`（已加入 .gitignore），只要不刪除這個目錄，下次直接照第一步指令重新啟動 Edge，通常不需要再次登入（除非 session 已在伺服器端過期）。

## 7. 給 Phase 2 的建議（已完成，見第 8 節）

- 完整原始資料（含 outerHTML、xpath、cssPath）已寫入 `config/selectors.discovered.json`，Phase 2 的 `src/trip_form.py` 應以此檔案為主要依據，而非重新猜測 selector。
- 若欄位 id 看起來像 ASP.NET WebForms 自動產生的長 id（例如 `ctl00_ContentPlaceHolder1_txtDate`），優先用 `id` 或 `name` 精確匹配，避免用文字內容做選擇（文字可能因語系/版本而變動）。
- 若表單位於 iframe 或 popup 內，Phase 2 填表前務必先取得對應的 `Frame`/`Page` 物件，再對該物件操作，不能直接對最外層 `page` 操作。
- 送出前所有欄位務必先做「必填檢查」與「內容回顯確認」，並等待使用者輸入 `y` 才能呼叫送出按鈕，任何情況下都不可自動送出。

## 8. 人工驗證後的欄位對照表（`ESSF21` 出差登記表單）

自動掃描對這個 ESS 模組的 label 猜測大多失敗（不是標準 `<td>` 排版），以下是實際捲動畫面、
比對 DOM 座標後人工驗證過的對照表。表單所在 frame：

`http://eip.example.com/HRMESS/src/ESS/ESSF21/ESSF21.aspx?...`（frame name: `framePlus`）

| 使用者輸入欄位 | 畫面標籤 | 對應 id | 型態 | 備註 |
|---|---|---|---|---|
| 出差日期（開始） | 開始日期 | `ESSCCDJ024_txt` | text，格式 `YYYY/MM/DD` | 旁邊有 `...` 按鈕開日期選擇器，直接 `.fill()` 應該也可以 |
| 開始時間 | 開始時間 | `ESSCCDJ025_txt` | text，格式 `HH:mm` | 同上，旁邊也有 `...` 按鈕 |
| 出差日期（結束） | 結束日期 | `ESSCCDJ026_txt` | text，格式 `YYYY/MM/DD` | 若使用者只給一個日期，開始/結束日期都填同一天 |
| 結束時間 | 結束時間 | `ESSCCDJ027_txt` | text，格式 `HH:mm` | |
| 出差地點 | 出差地點 | `ESSCCDJ028_txt` | **textarea** | 目前預設空白 |
| 出差事由 | 出差原因 | `ESSCCDJ037_txt` | **textarea** | 使用者說的「出差事由」對應畫面上的「出差原因」 |
| 備註 | 備註 | `ESSCCDJ029_txt` | **textarea** | |
| （無對應欄位） | — | — | — | **這個表單沒有「交通方式」欄位**，見下方說明 |

其他觀察到、但使用者流程不需要填的欄位：

| 畫面標籤 | 對應 id | 說明 |
|---|---|---|
| 出差類別 | 顯示文字 `ESSCCDJ022_txt`（唯讀顯示）＋代碼 `ESSCCDJ020_txt` / `ESSCCDJ021_txt` | 預設值「701 平日出差」。使用者的填寫流程沒有指定出差類別，所以 `trip_form.fill_form()` 刻意不去動這個欄位，保留系統預設值。若未來需要改這個欄位，才需要另外測試是否能直接 `.fill()` 還是要模擬點擊 `...` 彈窗 |
| 扣除休息班次 / 扣除非在崗時間 / 扣除休息班次內加班就餐段 | `ESSCCDJ023_chk` / `ESSCCDJ023_1_chk` / `ESSCCDJ038_chk` | 3 個 checkbox，目前預設只勾選第 3 個。使用者流程沒有提到這些，Phase 2 應保留預設值，不要主動勾/取消 |
| 出差申請 | `ESSCCDJ018_txt` | 唯讀（灰底），目前是「直接登記」模式所以不需填 |
| 填單人／填單人公司／部門／職位／填單日期／申請人 | `ESSCCDJ004~015`, `ESSCCDJ033~035` | 系統依登入者自動帶入，不需要也不應該覆寫 |
| 出差明細（表單最下方的表格） | `ESSCCDD001~016`（透過 `GridUserControl1` 操作） | 列出「出差人」清單，目前是空的；`直接登記` 模式下似乎不強制要填，但送出前應確認是否為必填 |

### ⚠️ 沒有「交通方式」欄位

實際畫面（`screenshots/04_form_fields_body.png`）從上到下依序是：
出差申請 → 出差類別（含 3 個 checkbox） → 開始/結束日期時間 → 出差地點 → 出差原因 → 備註 → 出差明細表。

**整個出差登記表單沒有「交通方式」這個欄位（已確認，非猜測）。** 有一個第 4 個隱藏的 textarea
（`ESSCCDJ036_txt`，`offsetParent === null`，畫面上不可見），原本猜測可能是「彈性欄位」功能保留的欄位。
實際點擊畫面上的「彈性欄位」按鈕（`GridUserControl1_BtnExtraField`）確認：該按鈕是 `disabled` 狀態，
其 `onclick` 內容是 `alert('該作業尚未設定彈性欄位!')`——也就是這個表單的彈性欄位功能根本沒有被系統管理者
設定，`ESSCCDJ036_txt` 目前用不到，也不會顯示任何標籤。

**結論**：這個 EIP 出差登記表單就是沒有交通方式欄位。建議把交通方式資訊附加寫進「備註」欄位
（例如「備註：Q3 MongoDB 維護作業；交通方式：捷運」）。若一定要有獨立的交通方式欄位，需要請
EIP 系統管理者在後台設定「彈性欄位」，這超出本工具能自動化的範圍。

## 9. Phase 2 實作與驗證結果

Phase 2 已經實作並在真實登入的畫面上實測（只測填表，全程未點擊任何送出/儲存按鈕）：

- `src/eip_client.py`：`open_trip_form(page)` 會自動點擊上方工具列的「出差登記」捷徑（banner frame 內
  `td#tdMenu_1 > table > tbody > tr > td:nth-of-type(2)`），並等待表單的 iframe
  （`ESS/ESSF21/ESSF21.aspx`）真正載入完成才回傳，重跑時若表單已經開著會直接沿用，不會重複點擊。
- `src/trip_form.py`：`fill_form()` 依第 8 節對照表填入 開始/結束日期時間、出差地點、出差原因，並把
  交通方式併入備註；`check_required_fields()` 讀回這些欄位確認都有值；`submit_form()` 點擊表單外層
  frame（`EPI/EPIE001/EPIE001.aspx`）裡的 `#MasterPage_btnCreateToolSendForm`。
- **送出按鈕已確認、非猜測**：直接讀取按鈕的 `title` 屬性（沒有點擊，純讀取 DOM），
  `MasterPage_btnCreateToolSendForm` 的 `title="傳送"`，`MasterPage_btnCreateToolSaveForm` 的
  `title="草稿儲存"`——確認前者才是真正的「送出」動作，本工具使用前者。
- **實測結果**：用使用者提供的範例資料（`2026/08/12 09:00–17:30／富邦金控／MongoDB 系統維護／
  捷運／Q3 MongoDB 維護作業`）呼叫 `fill_form()`，畫面截圖見
  `screenshots/08_phase2_fill_test_scrolled.png`，所有欄位都填到正確位置，
  `check_required_fields()` 回傳空清單（無缺漏）。全程未呼叫 `submit_form()`。
- `src/main.py` 的送出流程有兩層確認：填單前的資料摘要確認（第一次 `y`），以及填完表單、
  從瀏覽器讀回實際內容顯示給使用者看之後的最終確認（第二次 `y`），只有兩次都輸入 `y`
  才會呼叫 `submit_form()`。

## 10. 2026-08 架構修正與技術驗證

實際運作過程中發現幾個原始設計沒考慮到的風險（重複送出、session 過期時仍繼續操作、
對話框無差別 accept），做了一次完整的架構檢討與修正。新增/修改的模組：

| 模組 | 功能 | 對應問題 |
|---|---|---|
| `src/session.py` | `check_session(page)` 回傳 AUTHENTICATED/EXPIRED/UNKNOWN | 舊版只檢查 URL 是否含 `example.com`，連登出頁都會誤判為有效 session |
| `src/state_machine.py` | `TripFlow` 明確狀態機（AUTHENTICATED→FORM_OPEN→FORM_FILLED→TRAVELER_SAVED→READY_TO_SEND→SENDING→SENT，任何步驟可轉 SESSION_EXPIRED/FAILED） | 舊版是線性函式呼叫，沒有明確的「目前在哪一步」；轉入 SESSION_EXPIRED 會立即拋出例外，禁止任何自動重送 |
| `src/dialog_handler.py` | `DialogRecorder` 依 dialog 類型與訊息關鍵字分類處理 | 舊版 `submit_form()` 對任何 dialog 無條件 accept，有誤送風險；現在 beforeunload 自動接受，confirm 只在訊息不含「已存在/重複/覆蓋/錯誤/失敗/逾時/過期」等關鍵字時才接受，alert/prompt 一律不自動接受 |
| `src/network_log.py` | `NetworkRecorder` 記錄「儲存」「傳送」的 request/response/requestfailed | 舊版完全沒有網路層記錄，除錯只能靠截圖猜測；Authorization/Cookie 一律遮罩，POST 只記欄位名稱不記值 |
| `src/duplicate_check.py` | `find_existing_submission()` 查詢「表單追蹤處理 > 原稿資料匣」是否已有相同日期/時間的單據 | 送出失敗或結果不明時，避免盲目重試造成重複送件；DOM 結構（`#tdBar4`、`GridView1`、`td[title]` 為單號）皆為即時探索確認，非猜測 |
| `trip_form.verify_submission()` | 用單據編號格式（`單據:ESSF21 出差登記 (數字)`）判斷 SUCCESS/FAILED/UNKNOWN | 舊版靠「畫面清空」推論成功，但 session 過期時畫面也會清空，曾實際造成誤判 |
| `trip_form.add_traveler()` | 正式函式化「填出差人編號→觸發驗證→點儲存」，內建 dialog + network 雙紀錄器 | 舊版這個動作只在對話中用一次性腳本做過，沒有寫進正式程式碼 |

### 技術驗證結果（Playwright 官方文件 + 實測）

- **`connect_over_cdp()` fidelity 確實較低**（官方文件原文："significantly lower fidelity than
  the Playwright protocol connection"），但改用 `launch_persistent_context(channel="msedge")`
  直接測試後**證實登入這一步無法用這個方式解決**——只要導覽是 Playwright 呼叫的，不管是不是
  真正的 Edge，一律撞 `ERR_INVALID_AUTH_CREDENTIALS`。CDP-attach 目前仍是登入階段唯一可行的
  workaround，這個限制與「是否為 CDP」有關，與瀏覽器種類、GPO 政策無關。
- **beforeunload dialog 的攔截不穩定是已知問題**，不是本專案設定錯誤。Playwright 官方 GitHub
  issue [#14431](https://github.com/microsoft/playwright/issues/14431)、
  [#14305](https://github.com/microsoft/playwright/issues/14305) 證實「導覽觸發的 beforeunload」
  攔截不穩定是長期存在、未完全解決的行為；`page.close(run_before_unload=True)` 觸發的
  beforeunload 才是官方文件保證支援的情境。`DialogRecorder` 仍嘗試自動接受，但架構上假設它
  可能失敗。
- **Chrome DevTools MCP**（Google 官方，2026-06 收錄進 Microsoft Learn 文件）適合作為探索/
  除錯輔助工具，但官方明確警告 auto-connect 模式會讓 agent 繼承目前 session（可能外洩 PII），
  EIP 涉及員工個資，若採用必須在受控環境使用、不掛接正式帳號 session。正式送出流程維持
  deterministic Playwright 程式，不讓任何 MCP/agent 直接操作。

### 整合測試中發現的真實 bug（附帶修正）

- `duplicate_check.find_existing_submission()` 會把側邊選單切到「表單追蹤處理」模式，這會讓
  當時開著的「出差登記」分頁內容變成不可見（不只是失焦，是真的 `display` 被隱藏），
  導致後續 `add_traveler()` 找不到欄位。修正：新增 `eip_client.reactivate_trip_form_tab()`，
  在查完重複後、操作表單前，先點擊 jQuery UI Tabs 的分頁錶頭（`#ESSF21`，在 `platform.aspx`
  frame 裡）把分頁切回前景。
- `duplicate_check` 的樹狀選單導覽邏輯原本假設每次都要先點 `#tdBar4` 才能進入追蹤模式，
  但如果側邊選單已經處於追蹤模式（例如同一個瀏覽器 session 裡前一次呼叫已經切換過），
  `#tdBar4` 根本不存在，點擊會逾時。修正：先檢查「原稿資料匣」文字是否已經可見，
  已經在追蹤模式就跳過點擊 `#tdBar4` 這一步。

以上兩個問題都是在真實 EIP 環境下跑整合測試時發現的，不是理論推測。
