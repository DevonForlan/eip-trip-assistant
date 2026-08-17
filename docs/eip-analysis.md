# EIP trip-registration - site exploration report

Generated: 2026-08-10 23:09:43 +0800

EIP URL: http://eip.example.com/EFNET/

## 1. Homepage structure

- Title: 電子簽核 (the portal's own title, verbatim)
- URL: http://eip.example.com/EFNET/
- Frame count: 16
- **Multiple frames detected (a classic frameset or nested iframes)**

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

## 2. The trip-registration trigger element

Searching for the text `出差登記` ("trip registration") found 6 candidate elements, ranked by likelihood. These are candidates, not a single guess - confirm the right one by hand:

| tag | type | id | name | label（推測） | text | frame | 建議 selector |
|---|---|---|---|---|---|---|---|
| a |  | ESSF21 |  |  | 出差登記.. | c/_Common/AppUtil/FrameSet/platform.aspx | `#ESSF21` |
| td |  |  |  |  | 出差登記(E.. | /_Common/AppUtil/FrameSet/titlebar1.aspx | `td#tdMenu_1 > table > tbody > tr > td:nth-of-type(2)` |
| span |  | DscLabel27_lbl |  |  | 出差登記 | FRM&AFormStatus=CREATE&ProductName=EFNET | `#DscLabel27_lbl` |
| a |  | RESTreet8 |  |  | 出差登記 | T/src/_Common/AppUtil/FrameSet/tree.aspx | `#RESTreet8` |
| font |  |  |  |  | 出差登記(ESSF21)(149) | T/src/_Common/AppUtil/FrameSet/tree.aspx | `div#treeUsedFunction > table > tbody > tr > td > a > font` |
| span |  | ESSCCDJ003_lbl |  |  | 出差登記ID | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ003_lbl` |

Full detail (including outerHTML / xpath) is written to `config/selectors.discovered.json`.

## 3. What happens on click

- The element that was actually clicked: tag=`a` id=`ESSF21` frame=`http://eip.example.com/EFNET/src/_Common/AppUtil/FrameSet/platform.aspx`

- Detected mode: **same_page_or_frame_unconfirmed**
  (No new window; the same Page either navigated or updated frame content.)
- Form page URL: http://eip.example.com/EFNET/
- Form page frame count: 16

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

## 4. Form fields

395 input / select / textarea / button elements found, scanning all frames recursively. Label and text cells quote the live page verbatim:

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

### Checkboxes (3)

| tag | type | id | name | label（推測） | text | frame | 建議 selector |
|---|---|---|---|---|---|---|---|
| input | checkbox | ESSCCDJ023_chk | ESSCCDJ023$chk |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ023_chk` |
| input | checkbox | ESSCCDJ023_1_chk | ESSCCDJ023_1$chk |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ023_1_chk` |
| input | checkbox | ESSCCDJ038_chk | ESSCCDJ038$chk |  |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ038_chk` |

### Radios (5)

| tag | type | id | name | label（推測） | text | frame | 建議 selector |
|---|---|---|---|---|---|---|---|
| input | radio | MasterPage_rblCreateToolImportant_0 | MasterPage$rblCreateToolImportant | 低 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_rblCreateToolImportant_0` |
| input | radio | MasterPage_rblCreateToolImportant_1 | MasterPage$rblCreateToolImportant | 普通 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_rblCreateToolImportant_1` |
| input | radio | MasterPage_rblCreateToolImportant_2 | MasterPage$rblCreateToolImportant | 高 |  | c/EPI/EPIE001/EPIE001.aspx?FormID=ESSF21 | `#MasterPage_rblCreateToolImportant_2` |
| input | radio | ESSCCDJ016_rdbl_0 | ESSCCDJ016$rdbl | 按申請登記 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ016_rdbl_0` |
| input | radio | ESSCCDJ016_rdbl_1 | ESSCCDJ016$rdbl | 直接登記 |  | FRM&AFormStatus=CREATE&ProductName=EFNET | `#ESSCCDJ016_rdbl_1` |

### Select options

- `ddlModule`：請選擇..(0), RES電子表單模組(RES), ESS PLUS模組(AppFormESS), 移動社交辦公(IMG)
- `DropDownList1`：繁體中文(Lang01), 簡體中文(Lang03)

## 5. Screenshots

- `screenshots/01_home_after_attach.png`
- `screenshots/02_before_click_trip_registration.png`
- `screenshots/03_trip_form_page.png`
- `screenshots/04_form_fields_body.png` - the application / trip category / dates and times / location / reason / remarks block (captured after scrolling by hand)
- `screenshots/05_form_detail_grid.png` - the traveler detail list at the bottom of the form (currently empty)

## 6. Session handling

- This analysis attached over CDP to an Edge that was launched and signed in to by hand; no session file is created or stored by this program.
- EIP requires Windows Integrated Authentication (NTLM/Negotiate). A browser Playwright launches itself cannot complete that handshake and surfaces no native credential prompt, so this attaches over the Chrome DevTools Protocol to an Edge that is already signed in, rather than using a Playwright-managed storage_state file.
- Edge uses its own profile directory `<project>\.edge-profile` (gitignored). As long as that directory survives, relaunching Edge with the same command usually needs no fresh sign-in, unless the server-side session has expired.

## 7. Notes for building the automation (done - see section 8)

- The full raw data (outerHTML, xpath, cssPath) is written to `config/selectors.discovered.json`. Base `src/trip_form.py` on that file rather than guessing selectors again.
- Where ids look like ASP.NET WebForms generated names (e.g. `ctl00_ContentPlaceHolder1_txtDate`), match exactly on `id` or `name` rather than on visible text, which can shift with locale or version.
- When the form lives in an iframe or popup, obtain that `Frame`/`Page` object first and operate on it - never on the outermost `page`.
- Before sending, always check required fields and read the values back from the live page for the user to confirm. Only call the send button after an explicit `y`; never send automatically.

## 8. Hand-verified field map (the `ESSF21` trip-registration form)

The automatic scan's label guesses mostly failed for this ESS module (it does not use a standard `<td>` layout), so the map below was verified by hand, scrolling the real screen and
comparing DOM coordinates. The form's frame:

`http://eip.example.com/HRMESS/src/ESS/ESSF21/ESSF21.aspx?...`（frame name: `framePlus`）

| User input | On-screen label | id | Type | Notes |
|---|---|---|---|---|
| trip date (start) | 開始日期 (start date) | `ESSCCDJ024_txt` | text, format `YYYY/MM/DD` | there is a `...` button beside it that opens a date picker, but `.fill()` should work directly |
| start time | 開始時間 (start time) | `ESSCCDJ025_txt` | text, format `HH:mm` | as above, also has a `...` button |
| trip date (end) | 結束日期 (end date) | `ESSCCDJ026_txt` | text, format `YYYY/MM/DD` | when the user gives only one date, start and end are both filled with it |
| end time | 結束時間 (end time) | `ESSCCDJ027_txt` | text, format `HH:mm` | |
| trip location | 出差地點 (trip location) | `ESSCCDJ028_txt` | **textarea** | blank by default |
| trip reason | 出差原因 (trip reason) | `ESSCCDJ037_txt` | **textarea** | what the user calls the trip's purpose maps to this label |
| remarks | 備註 (remarks) | `ESSCCDJ029_txt` | **textarea** | |
| (no matching field) | — | — | — | **this form has no transport field** - see below |

Other fields that were observed but that the user's flow never fills in:

| On-screen label | id | Notes |
|---|---|---|
| 出差類別 (trip category) | display text `ESSCCDJ022_txt` (read-only) plus codes `ESSCCDJ020_txt` / `ESSCCDJ021_txt` | defaults to "701 weekday trip". The user's flow never specifies a category, so `trip_form.fill_form()` deliberately leaves this field alone and keeps the system default. Changing it in future would need separate testing of whether `.fill()` works or the `...` popup has to be clicked |
| deduct rest shift / deduct off-post time / deduct meal breaks during overtime | `ESSCCDJ023_chk` / `ESSCCDJ023_1_chk` / `ESSCCDJ038_chk` | 3 checkboxes; by default only the third is checked. The user's flow never mentions them, so the defaults should be preserved rather than checked or unchecked deliberately |
| 出差申請 (trip application) | `ESSCCDJ018_txt` | read-only (greyed); not needed in the current "direct registration" mode |
| filer / filer's company / department / position / filing date / applicant | `ESSCCDJ004~015`, `ESSCCDJ033~035` | populated by the system from the signed-in user; neither necessary nor appropriate to overwrite |
| trip detail (the grid at the bottom of the form) | `ESSCCDD001~016` (driven through `GridUserControl1`) | lists the travelers, currently empty. It appears not to be mandatory in "direct registration" mode, but that should be confirmed before sending |

### ⚠️ There is no transport field

The real screen (`screenshots/04_form_fields_body.png`), top to bottom, is:
trip application → trip category (with its 3 checkboxes) → start/end dates and times → location → reason → remarks → the traveler detail grid.

**The whole trip-registration form has no transport field. Confirmed, not guessed.** There is a fourth hidden textarea
(`ESSCCDJ036_txt`, `offsetParent === null`, invisible on screen) that was initially guessed to be reserved for the "flexible fields" feature.
Clicking the flexible-fields button (`GridUserControl1_BtnExtraField`) settled it: the button is `disabled`, and
its `onclick` is an alert reading "no flexible fields have been configured for this operation" - so the feature was never
set up for this form by an administrator. `ESSCCDJ036_txt` is unused and displays no label.

**Conclusion**: this EIP trip-registration form simply has no transport field. The suggested approach is to append the transport
information to the remarks field (e.g. "remarks: Q3 MongoDB maintenance; transport: metro"). A dedicated transport field would
require an EIP administrator to configure flexible fields in the back office, which is beyond what this tool can automate.

## 9. Implementation and verification

The automation is implemented and was tested against a real signed-in screen (filling only - no send or save button was ever clicked):

- `src/eip_client.py`: `open_trip_form(page)` clicks the trip-registration shortcut in the top toolbar (inside the banner frame,
  `td#tdMenu_1 > table > tbody > tr > td:nth-of-type(2)`) and returns only once the form's iframe
  (`ESS/ESSF21/ESSF21.aspx`) has genuinely finished loading. On a re-run, an already-open form is reused rather than clicked again.
- `src/trip_form.py`: `fill_form()` fills the start/end dates and times, location and reason per the section 8 map, and folds
  the transport into the remarks; `check_required_fields()` reads those fields back to confirm each has a value; `submit_form()` clicks
  `#MasterPage_btnCreateToolSendForm` in the form's outer frame (`EPI/EPIE001/EPIE001.aspx`).
- **The send button is confirmed, not guessed**: reading the buttons' `title` attributes directly (DOM read only, no click),
  `MasterPage_btnCreateToolSendForm` has `title="傳送"` (send) and `MasterPage_btnCreateToolSaveForm` has
  `title="草稿儲存"` (save draft) - confirming the former is the real send action, which is what this tool uses.
- **Measured result**: calling `fill_form()` with the sample data the user provided (`2026/08/12 09:00-17:30 / <client site> /
  MongoDB system maintenance / metro / Q3 MongoDB maintenance`), screenshot at
  `screenshots/08_phase2_fill_test_scrolled.png`, put every value in the right place and
  `check_required_fields()` returned an empty list (nothing missing). `submit_form()` was never called.
- `src/main.py`'s send flow has two confirmation layers: a summary of the data before filling (the first `y`), and a final
  confirmation after the form is filled and the actual values have been read back off the browser and shown to the user (the second
  `y`). `submit_form()` is called only when both were `y`.

## 10. Architecture revision and technical verification, 2026-08

Running this for real surfaced several risks the original design had not accounted for (duplicate submission, carrying on after
the session expired, accepting dialogs indiscriminately), prompting a full architecture review. Modules added or changed:

| Module | What it does | The problem it addresses |
|---|---|---|
| `src/session.py` | `check_session(page)` returns AUTHENTICATED/EXPIRED/UNKNOWN | the old code only checked whether the URL contained `example.com`, so even the sign-out page counted as a valid session |
| `src/state_machine.py` | `TripFlow`, an explicit state machine (AUTHENTICATED→FORM_OPEN→FORM_FILLED→TRAVELER_SAVED→READY_TO_SEND→SENDING→SENT, with any step able to move to SESSION_EXPIRED/FAILED) | the old code was a linear sequence of calls with no explicit notion of "which step are we on". Entering SESSION_EXPIRED now raises immediately and forbids any automatic resend |
| `src/dialog_handler.py` | `DialogRecorder` classifies handling by dialog type and message keywords | the old `submit_form()` accepted any dialog unconditionally, risking an accidental send. Now beforeunload is auto-accepted, confirm is accepted only when the message contains none of the "already exists / duplicate / overwrite / error / failed / timed out / expired" keywords, and alert/prompt are never auto-accepted |
| `src/network_log.py` | `NetworkRecorder` records request/response/requestfailed around the save and send actions | there was no network-layer record at all before, leaving debugging to guesswork over screenshots. Authorization and Cookie are always masked, and POST logging keeps field names without values |
| `src/duplicate_check.py` | `find_existing_submission()` checks the document tracking view's draft folder for an existing document with the same date and time | avoids blind retries turning into duplicate submissions when a send fails or its outcome is unclear. The DOM structure (`#tdBar4`, `GridView1`, `td[title]` holding the document number) was confirmed by live exploration, not guessed |
| `trip_form.verify_submission()` | judges SUCCESS/FAILED/UNKNOWN from the document-number format | the old code inferred success from "the screen cleared", but an expired session clears the screen too, which had already caused one false reading |
| `trip_form.add_traveler()` | turns "enter the traveler code → trigger validation → click save" into a real function, with both the dialog and network recorders built in | this action had only ever been done by a one-off script in conversation, never written into the production code |

### Technical verification (Playwright's own docs plus measurement)

- **`connect_over_cdp()` really does have lower fidelity** (the docs' words: "significantly lower fidelity than
  the Playwright protocol connection"), but testing `launch_persistent_context(channel="msedge")`
  directly **proved that this does not solve the sign-in step** - any navigation Playwright initiates hits
  `ERR_INVALID_AUTH_CREDENTIALS`, real Edge or not. CDP attach remains the only workable route for
  sign-in; the restriction turns on whether CDP is involved, not on the browser or GPO policy.
- **Unreliable interception of beforeunload dialogs is a known issue**, not a misconfiguration here. Playwright's GitHub
  issue [#14431](https://github.com/microsoft/playwright/issues/14431)、
  [#14305](https://github.com/microsoft/playwright/issues/14305) confirms that intercepting a navigation-triggered beforeunload
  has long been unreliable and is not fully resolved; only the beforeunload triggered by
  `page.close(run_before_unload=True)` is a scenario the docs guarantee. `DialogRecorder` still tries to accept
  automatically, but the architecture assumes it may fail.
- **Chrome DevTools MCP** (Google's own, added to the Microsoft Learn docs in 2026-06) suits exploration and
  debugging, but its documentation warns explicitly that auto-connect mode lets an agent inherit the current session (potentially
  leaking PII). EIP handles employee personal data, so adopting it would require a controlled environment and no production
  account session. The production send flow stays deterministic Playwright code, with no MCP or agent driving it directly.

### Real bugs found during integration testing (fixed along the way)

- `duplicate_check.find_existing_submission()` switches the sidebar into document-tracking mode, which makes the
  currently open trip-registration tab's content invisible - not merely unfocused, but genuinely `display`-hidden -
  so the following `add_traveler()` could not find its fields. Fix: added `eip_client.reactivate_trip_form_tab()`,
  which clicks the jQuery UI Tabs header (`#ESSF21`, in the `platform.aspx` frame) to bring the tab back to the
  foreground after the duplicate check and before touching the form.
- `duplicate_check`'s sidebar navigation assumed `#tdBar4` always had to be clicked to enter tracking mode, but when
  the sidebar is already in tracking mode (e.g. a previous call in the same browser session already switched it),
  `#tdBar4` does not exist at all and the click times out. Fix: check first whether the draft-folder text is already
  visible, and skip the `#tdBar4` click when tracking mode is already active.

Both were found running integration tests against the real EIP, not reasoned about in the abstract.
