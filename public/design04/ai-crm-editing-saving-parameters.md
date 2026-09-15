# AI CRM Mobile WebApp — Editing & Saving 動效參數規格書 Vol.2
> 供 AI Agent (Cursor / Copilot / Claude Code) 實作參考

---

## Inline Editing 效果參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | 觸發條件 |
|---|---|---|---|---|---|
| 1 | 點擊即編輯 Click-to-Edit | 150ms | ease | box-shadow: 0→0 0 0 3px accent; border-color 漸現 | onClick 切換 span/input 顯示 |
| 2 | 雙擊編輯表格單元 | 200ms | ease | background: transparent→rgba(accent,.12); transform: scale(1→1.02) | ondblclick 啟用 contentEditable |
| 3 | 浮動標籤 Floating Label | 200ms | ease | top: 22px→2px; font-size: 12px→10px; color→accent | onFocus / onBlur（無值才還原） |
| 4 | 拖曳排序 Drag Handle | 200ms | ease | transform: scale(1→1.03); box-shadow: 0→0 8px 20px rgba(0,0,0,.4) | onMouseDown/Up 或 dragstart/dragend |
| 5 | 富文本工具列浮現 | 250ms | ease | opacity: 0→1; transform: translateY(-6px→0) | onSelect 顯示，onBlur 隱藏 |

---

## Save 按鈕狀態參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | 狀態流程 |
|---|---|---|---|---|---|
| 6 | Save → Spinner → Check | 700ms(轉換) + 1000ms(停留) | ease | background 漸變 accent→ok；文字置換 | idle → saving → success → idle |
| 7 | 按鈕形變 Morph 為圖示 | 350ms | cubic-bezier(.4,0,.2,1) | width: 90px→36px；border-radius: 10px→50% | idle → morphing → success → idle |
| 8 | 進度填滿按鈕 | 1400ms | linear | width: 0%→100%（內層 span 填色） | onClick 觸發填滿，完成後重置 |
| 9 | 未變更即disable儲存 | 250ms | ease | opacity: .35→1；background 灰階→漸層色 | oninput 偵測變更啟用按鈕 |
| 10 | SVG 勾號描邊動畫 | 500ms(圓) + 300ms(勾,延遲400ms) | ease | stroke-dashoffset: 69→0 / 16→0 | onClick 觸發，1.8s後還原 |

---

## Autosave 自動儲存參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | debounce |
|---|---|---|---|---|---|
| 11 | 頂部細線 Autosave Bar | 500ms(填滿) + 400ms(淡出) | ease | width: 0→100%；opacity: 1→0→1 | 300ms |
| 12 | 狀態文字漸變切換 | 250ms/次(共3段) | ease | opacity: 0↔1 交叉切換文字內容 | 600ms |
| 13 | 雲端同步脈動指示 | 600ms(blink loop) + 1000ms(同步) | ease | animation: blink .6s infinite；background 色改變 | 事件觸發即開始 |
| 14 | 自動儲存後 Undo Toast | 300ms | cubic-bezier(.34,1.56,.64,1) | transform: translateY(50px→0)；opacity: 0→1 | 顯示2.2秒後自動收回 |

---

## 驗證／協作回饋參數

| # | 效果名稱 | duration | easing | 核心 CSS 屬性 | 觸發事件 |
|---|---|---|---|---|---|
| 15 | 欄位錯誤震動提示 | 350ms | keyframes shake | transform: translateX(0,-6px,6px,-4px,0)；border-color→danger | 驗證失敗 onClick |
| 16 | 即時輸入驗證勾號 | 200ms | ease | opacity: 0→1（符合條件即顯示✓） | oninput 即時判斷 |
| 17 | 協作者即時游標／頭像 | 1200ms | ease-in-out | top/left 隨機位移，模擬多人協作在線狀態 | 模擬事件或 WebSocket push |
| 18 | AI 建議 Ghost Text | 即時（無transition，跟隨輸入） | — | 淺色文字疊加於 input 上方，as-you-type 更新 | oninput，按 Tab 採納建議 |

---

## 全域參數建議（Editing / Saving 場景）

### 儲存回饋速度分級
- 即時驗證回饋（勾號/紅框）：150–250ms
- Autosave debounce 延遲：300–900ms（避免過於頻繁觸發 API）
- Save 按鈕 loading → success 停留時間：600–1000ms（讓使用者確實感知完成）
- Undo/Toast 顯示時長：2000–2500ms 後自動消失

### 狀態機建議（Save Button）
```
idle → (onClick) → saving → success → idle
                       ↓
                     error → idle (顯示錯誤原因並允許重試)
```

### Autosave 最佳實踐
- 使用 debounce 而非 throttle，避免使用者仍在輸入時就送出請求[web:22][web:26]
- 狀態標籤建議循環：「編輯中」→「儲存中」→「已儲存 · 剛剛」，並保留時間戳記增加信任感[web:26]
- 提供 Undo 選項而非僅依賴自動化，平衡便利性與使用者控制感[web:22]

### AI 協作編輯建議
- Ghost text／AI 建議應使用比一般文字淺 40–50% 的顏色（如 #4a5068 對比主文字色），避免與真實輸入混淆[web:33]
- 多人協作游標應附加使用者名稱縮寫或頭像，並使用不同色彩區分身份[web:29]
- 所有 AI 建議應可用單一按鍵（如 Tab）快速採納或用 Esc 忽略，降低操作成本[web:23][web:24]

### Accessibility 補充
- 驗證錯誤震動動畫應同時搭配 `aria-live="polite"` 文字提示，避免僅依賴視覺動畫傳達錯誤
- `prefers-reduced-motion` 條件下，shake 動畫應降級為單純邊框顏色變化

---

*對應範例網站：ai-crm-editing-saving-demo.html — 18個可互動體驗的 Editing/Saving 動效原始碼*
*搭配第一份文件：ai-crm-uiux-demo.html（24個開啟/轉頁/Menu動效）與 ai-crm-uiux-parameters.md*
