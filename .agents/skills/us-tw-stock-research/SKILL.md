---
name: us-tw-stock-research
description: >-
  Orchestrate US and Taiwan stock research by combining last30days-skill
  (social sentiment), daily_stock_analysis (multi-market fundamentals/technicals),
  and day-trader-skill (setups, simulation, and strict risk gates) using AGY
  model tiers (flash_lite, flash, pro).
---

# 美股與台股多模型協作研究 Skill

當使用者要求分析美股（如 `NVDA`、`AAPL`）或台股（如 `2330`、`2330.TW`、`2317`）時，嚴格遵循以下兩階段執行契約：

## 階段一：平行取得資訊（使用 `flash_lite`）
1. **市場識別**：
   - 純數字代號（4~6 碼）或 `.TW`/`.TWO` 結尾 $\rightarrow$ 歸類為 **台股（TW）**。
   - 英文字母代號 $\rightarrow$ 歸類為 **美股（US）**。
2. **平行採集**：
   - **輿情面（`last30days-skill` 模式）**：檢索近 30 天 Reddit、X、HN（美股）或 PTT Stock / 財經新聞（台股）高互動討論，依互動熱度排序並去重。
   - **行情與籌碼面（`daily_stock_analysis` + `day-trader-skill` 模式）**：
     - 美股：近期 OHLCV、關鍵均線（20MA/60MA）、量比、近期新聞與 SEC 申報異動。
     - 台股：近期 OHLCV、三大法人買賣超、融資餘額變化與最近一期月營收年增率。

## 階段二：分工分析（使用 `flash`）
將階段一的乾淨數據分派給三個獨立分析視角，互不干擾：
1. **輿情與催化劑視角**：區分「實質利多/財報催化」與「社群 FOMO 情緒」。
2. **技術與進出場視角**：標定趨勢方向、關鍵支撐/壓力、突破觸發點與建議停損位。
3. **基本面與籌碼視角**：評估估值位階與大戶/法人動向。

## 階段三：總審與風控閘道（使用 `pro`）
由高推理模型（`pro`）扮演 `Portfolio & Risk Judge`：
- 交叉比對階段二的三份報告，明確指出多空矛盾點。
- **強制風控檢查（承襲 `trader-risk`）**：
  - 未設定明確停損價位 $\rightarrow$ 禁止建議進場。
  - 預估盈虧比（Reward/Risk）低於 `2.0` $\rightarrow$ 降級為「觀望」。
  - 台股標的須額外標註 10% 漲跌幅與隔日跳空鎖死風險。
- **安全邊界**：本系統僅產出決策建議與模擬單，**絕不自動下單**，任何執行動作必須等待使用者明確回覆確認。
