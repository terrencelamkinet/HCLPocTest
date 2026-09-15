# AI CRM Mobile WebApp — AI-Driven 互動效果參數規格書 Vol.3
> 供 AI Agent (Cursor / Copilot / Claude Code) 實作參考

---

## AI 思考／串流狀態參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | 觸發條件 |
|---|---|---|---|---|---|
| 1 | 思考中三點跳動 | 1.4s loop | ease-in-out | transform: translateY(0→-6px); opacity: .4→1（三點延遲.2s/.4s） | AI 開始處理請求時顯示 |
| 2 | 串流打字機文字 | ~35ms/字 | linear | 逐字 append 至 textContent；可用 requestAnimationFrame 取代 setInterval | LLM 回應 chunk 到達時觸發 |
| 3 | Shimmer 骨架載入條 | 1.4s loop | linear | background-position: -200px→200px；background-size: 400px 100% | AI 分析結果未回傳前 |
| 4 | 脈動光暈 AI 頭像 | 1.6s loop | ease-in-out | box-shadow: 0 0 0 0→0 0 0 6px rgba(accent,0) | AI 助理運算中持續顯示 |
| 5 | 進度百分比運算提示 | 600ms/階段，共4階段 | ease | 文字內容置換 + 數字遞增 | 批量 AI 任務（如評分重算） |
| 6 | 取消／中斷 AI 生成 | 即時 | — | button 文字狀態切換，中斷 stream 連線 | 用戶主動點擊停止 |

---

## AI 建議與可解釋性參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | 設計原則 |
|---|---|---|---|---|---|
| 7 | Next Best Action 卡片 | — | — | 卡片含信心分數 + 理由 + 明確標題 | 建議需附上下文依據，非純黑盒推薦 |
| 8 | AI 建議淡入清單 | 300ms/項，間隔120ms | ease | opacity: 0→1; transform: translateX(-10px→0) | 避免多筆建議同時湧現造成資訊過載 |
| 9 | 信心分數環形指示 | 1s（數字遞增）+ stroke動畫 | ease | stroke-dashoffset 插值；數字用 setInterval 遞增 | 視覺化信心度比純數字更快建立信任 |
| 10 | 理由展開 Tooltip | 300ms | ease | max-height: 0→40px（配合 overflow:hidden） | 預設收合，避免佔用主畫面空間 |
| 11 | AI 標籤浮水印 | 200ms | ease | transform: scale(1→1.1) on hover | 標示 AI 生成內容來源，強化透明度 |
| 12 | 接受／修改／拒絕操作條 | 即時 | — | 三按鈕並列，採納後文字/樣式即時反饋 | 遵循「建議優先、強制最少」原則 |

---

## AI 入口與擺位模式參數

| # | 效果名稱 | 擺位邏輯 | 適用場景 | 設計原則 |
|---|---|---|---|---|
| 13 | 右下角浮動 AI 按鈕 | position: fixed; bottom/right: 20-40px | 一般企業 CRM 後台 | 業界標準位置，符合用戶既有瀏覽慣性，不遮擋主內容[web:56] |
| 14 | AI-First Hero 提示輸入框 | 頁面正中央，首屏第一視覺焦點 | AI 為核心產品（如 AI 助理型 CRM） | 僅當 AI 即是主產品互動方式時才置於最高層級位置[web:61] |
| 15 | 側邊欄常駐 AI 面板 | 固定側邊，與主表格並排 | 需持續參考 AI 洞察的分析工作流 | AI 輔助但不佔用主任務區域 |
| 16 | 內嵌卡片式 AI 摘要 | 嵌入既有儀表板卡片內 | 日常任務流內的快速洞察 | AI 融入任務流，而非成為另一個目的地[web:44] |

---

## AI 存在感與個人化參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | 觸發條件 |
|---|---|---|---|---|---|
| 17 | AI 主動打招呼氣泡 | 350ms | ease | opacity: 0→1; transform: translateY(6px→0) | 進入頁面後延遲2-3秒觸發，非強制彈窗 |
| 18 | AI 個人化排序提示 | 400ms | ease | background 高光色暫時套用，1.5s後淡除 | 列表因個人化重新排序時 |
| 19 | 語音輸入波形回饋 | 100ms/次更新 | linear | height: 隨機4-24px 模擬音量 | 按住語音輸入按鈕期間持續更新 |
| 20 | AI 學習中徽章 | 1s loop | ease | opacity: 1↔.3（狀態指示點閃爍） | 偵測用戶重複修正建議後顯示 |

---

## AI 元件擺位總則（重要設計判斷）

### 一般網站是否把 AI 放在「第一位置」？
答案是**視產品定位而定，多數企業 SaaS／CRM 不會**：

- **AI 是輔助層（多數 CRM／企業後台採用）**：AI 入口放在**右下角浮動按鈕**（業界慣例，符合用戶預期路徑，不遮擋核心資料）[web:56][web:53]，或以**側邊面板／內嵌卡片**形式融入既有任務流，因為企業用戶進入系統的首要目的是查看客戶資料、儀表板，AI 是輔助決策工具而非主體驗[web:44][web:50]。
- **AI 是主產品本身（AI-first 工具採用）**：如 v0、Perplexity 等產品，AI 提示輸入框才會放在首頁最中心、第一屏最大視覺焦點，因為「與AI對話」本身就是核心操作[web:61]。
- **混合模式**：部分 2026 SaaS 產品在首頁 Hero 區塊加入 AI 驅動的個人化內容或互動式 Demo，但實際功能入口仍保留在次要位置，Hero 僅作為「展示 AI 能力」的行銷用途，非日常操作入口[web:52][web:58]。

### 實作建議
- 企業 CRM 預設放置：AI Chat／建議入口 = 右下角固定按鈕，離邊緣 20–40px，滾動時保持可見[web:56]
- 若頁面已有 cookie banner 或其他固定元件佔用右下角，改用左下角並保持一致性[web:56]
- AI 建議內容應直接嵌入相關資料卡片（inline），只有開放式問答才需要獨立聊天視窗[web:65]
- Mobile 版本 AI 聊天視窗全螢幕僅在「使用中」狀態展開，閒置時收回為小圖示，避免佔用寶貴垂直空間[web:53]

### Streaming 文字實作細節
- 建議速度：5ms/字符（約200字/秒）為最適合閱讀且不顯拖沓的速度[web:60]
- 應將「網路串流」與「視覺顯示」解耦：先 buffer 收到的 chunk，再以固定速度逐字顯示，避免網路延遲造成畫面卡頓[web:60]
- 使用 requestAnimationFrame 而非 setInterval 可確保與螢幕刷新率同步，畫面更流暢[web:60][web:66]

### Accessibility 補充
- 思考中動畫（三點跳動、shimmer）應搭配 `aria-live="polite"` 宣告「AI 正在處理」文字
- 語音波形回饋需提供純文字替代狀態（如「正在聆聽...」）供螢幕閱讀器使用
- `prefers-reduced-motion` 下，shimmer/glow 動畫應降級為靜態透明度變化

---

*對應範例網站：ai-crm-ai-driven-demo.html — 20個可互動體驗的 AI-Driven 動效原始碼*
*系列文件：Vol.1（開啟/轉頁/Menu）、Vol.2（Editing/Saving）、Vol.3（AI參與效果，本文件）*
