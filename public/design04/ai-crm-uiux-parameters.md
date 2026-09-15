# AI CRM Mobile WebApp — UI/UX 動效完整參數規格書
> 供 AI Agent (Cursor / Copilot / Claude Code) 實作參考

---

## 開啟／啟動效果參數

| # | 效果名稱 | duration | easing (cubic-bezier) | 核心 CSS 屬性 | 觸發條件 |
|---|---|---|---|---|---|
| 1 | Logo 縮放淡入 | 600ms | cubic-bezier(.34,1.56,.64,1) | transform: scale(.4→1); opacity: 0→1 | App mount, 首屏載入 |
| 2 | 漸層進度條 | 1400ms | ease | width: 0%→100%; background: linear-gradient | API 資料請求期間 |
| 3 | Skeleton 骨架屏 | 1200ms (loop) | ease-in-out (pulse) | opacity: .5↔1 (animation: pulse) | 資料未回傳前，逐格延遲 150ms |
| 4 | 圓形擴散揭幕 | 800ms | ease | clip-path: circle(0%→150% at 50% 50%) | 頁面初次渲染完成 |
| 5 | 卡片逐一浮現 | 350ms/項，間隔80ms | ease | opacity: 0→1; transform: translateY(14px→0) | Dashboard KPI 卡片載入 |
| 6 | 模糊轉清晰進場 | 700ms | ease | filter: blur(8px→0); opacity: .5→1 | AI 運算結果揭示 |

---

## 轉頁效果參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | 方向邏輯 |
|---|---|---|---|---|---|
| 7 | iOS 橫向推移 | 300ms | cubic-bezier(.4,0,.2,1) | transform: translateX(100%→0) 新頁；舊頁 0→-30% | Push=右進左出，Pop=反向 |
| 8 | 淡出淡入交叉 | 250ms | ease | opacity: 交叉 0↔1 | Tab 切換用 |
| 9 | 共享元素縮放 | 500ms | cubic-bezier(.4,0,.2,1) | width/height/border-radius 插值動畫 | 列表項目→詳情頁 |
| 10 | 卡片堆疊 3D | 450ms | cubic-bezier(.34,1.56,.64,1) | transform: translateY(100%→0) scale(.95→1) | Modal-like push |
| 11 | 3D 翻頁 | 600ms | ease | transform: rotateY(0→180deg); backface-visibility: hidden；perspective: 800px (父層) | 圖表視角切換 |
| 12 | 模糊景深轉場 | 400ms (出) + 400ms (進) | ease | filter: blur(0→6px); opacity: 1→0，接續反向 | AI分析中→結果 |
| 13 | 底部 Modal Sheet | 350ms | cubic-bezier(.34,1.56,.64,1) | transform: translateY(100%→0); border-radius: 16px 16px 0 0 | 快速編輯彈出 |

---

## Menu 收放效果參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | 附加邏輯 |
|---|---|---|---|---|---|
| 14 | 側邊 Drawer | 300ms | cubic-bezier(.4,0,.2,1) | transform: translateX(-100%→0); overlay opacity: 0→.5 | 同步觸發 overlay + hamburger icon |
| 15 | 底部 Bottom Sheet | 300ms | cubic-bezier(.34,1.56,.64,1) | transform: translateY(100%→0) | 支援手勢下滑關閉 |
| 16 | 漢堡轉X圖示 | 300ms | ease | 上下線: rotate(±45deg) + translateY(6px)；中線: opacity 0 | class toggle 驅動 |
| 17 | 全螢幕縮放淡入 | 300ms | ease | opacity: 0→1; transform: scale(.9→1) | 覆蓋 z-index 最高層 |
| 18 | Stagger 展開選單 | 300ms/項，間隔60ms | cubic-bezier(.34,1.56,.64,1) | opacity: 0→1; transform: translateX(-16px→0) | 逐項 setTimeout(60*i) |
| 19 | Radial FAB 選單 | 350ms | cubic-bezier(.34,1.56,.64,1) | transform: translate(0,0→offset); opacity: 0→1 | 弧形座標預先計算 |

---

## 微互動回饋參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | 觸發事件 |
|---|---|---|---|---|---|
| 20 | 按鈕 Ripple | 400–500ms | ease | transform: scale(0→14); opacity: 1→0 | onClick, 位置=觸點座標 |
| 21 | 下拉刷新 | 600ms | ease | transform: rotate(0→720deg) | Pull gesture release |
| 22 | Tab 底線滑動 | 300ms | cubic-bezier(.4,0,.2,1) | transform: translateX(位置插值) | Tab index 改變 |
| 23 | Toast 通知滑入 | 350ms (入) + 停留1200ms + 350ms(出) | cubic-bezier(.34,1.56,.64,1) | transform: translateY(-40px→8px); opacity: 0→1 | 系統事件觸發，自動消失 |
| 24 | 按下縮放回饋 | 150ms | ease | transform: scale(1→.92→1) | onTouchStart / onTouchEnd |

---

## 全域參數建議（AI Agent 實作準則）

### 速度分級
- 微互動：100–200ms
- Menu / Tab 切換：250–350ms
- 轉頁 / Modal：250–450ms
- 啟動動畫：600–1400ms（超過1秒需搭配可視進度反饋）

### 統一 Easing 曲線
- 一般過渡：`cubic-bezier(.4,0,.2,1)`（Material Standard curve）
- 彈跳／強調效果：`cubic-bezier(.34,1.56,.64,1)`（Overshoot curve）
- 避免混用超過2種曲線，以維持品牌一致性

### GPU 加速屬性
- 優先使用 `transform` 與 `opacity` 觸發動畫
- 避免直接改變 `width` / `height` / `top` / `left` 造成 reflow
- 確保 60fps 流暢度

### 可及性（Accessibility）
- 所有動畫應包裝於 `@media (prefers-reduced-motion: reduce)` 條件內
- 降級為即時切換或縮短至 0–50ms

### 手勢優先
- Drawer / Bottom Sheet 應同時支援手勢滑動關閉（非僅按鈕）
- 滑動超過閾值（如40%高度/寬度）時自動完成動畫而非彈回

### 狀態管理建議
- 每個動效觸發需綁定單一 state（如 `isOpen: boolean`）
- 避免同時多次觸發造成動畫堆疊衝突
- 建議加入 debounce（150ms）防止重複點擊

---

*對應範例網站：ai-crm-uiux-demo.html — 24個可互動體驗的動效原始碼*
