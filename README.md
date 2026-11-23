# 美股 & 台股多代理投研系統（AGY Multi-Model Orchestration）

整合三個開源專案的設計精髓，並基於 **Google Antigravity (AGY)** 的 Subagent / `run_workflow` 模型分級機制實作：

1. **`last30days-skill`**：近 30 天跨平台社群輿情（Reddit、X、HN、YouTube、Polymarket）
2. **`daily_stock_analysis`**：台股（TWSE/TPEX via AkShare/YFinance）與美股多維度體檢、技術指標、歷史快照與推播
3. **`day-trader-skill`**：美股盤中掃描、SEC/國會揭露、10,000 次盤中模擬（Time Machine）與嚴格風控護欄（Human-in-the-loop）

---

## AGY 模型分級與分工策略

| 階段 | 角色名稱 | AGY 模型 (`model`) | 職責說明 | 對應來源 Repo |
| :--- | :--- | :--- | :--- | :--- |
| **階段一：資訊採集** | `News & Social Scraper` | `flash_lite` | 高併發抓取近 30 天美/台股社群討論、新聞標題去重與格式清洗 | `last30days-skill` |
| **階段一：資訊採集** | `Market Data Collector` | `flash_lite` | 依市場路由拉取美股（YFinance/SEC）與台股（TWSE/櫃買/法人籌碼）硬數據 | `daily_stock_analysis` / `day-trader-skill` |
| **階段二：分工分析** | `Sentiment & Catalyst Analyst` | `flash` | 判讀輿情熱度、Polymarket 賠率、法說會/財報催化劑與 FOMO 風險 | `last30days-skill` + `trader-news` |
| **階段二：分工分析** | `Technical & Setup Analyst` | `flash` | 計算均線、量價結構、支撐壓力與日內型態（美股含開盤區間突破） | `daily_stock_analysis` + `trader-entry` |
| **階段二：分工分析** | `Fundamental & Chip Analyst` | `flash` | 美股檢視 SEC 揭露與估值；台股檢視三大法人買賣超、融資券與月營收 | `trader-analyst` + `daily_stock_analysis` |
| **階段三：總審風控** | `Portfolio & Risk Judge` | `pro` | 綜合三方報告解決多空衝突、檢核停損與盈虧比（`trader-risk` 規則），產出需人工確認的最終決策單 | `trader-risk` + `src/analyzer.py` |

---

## 美股 vs 台股 差異化處理

* **美股（US）**：支援盤前/盤中掃描、SEC EDGAR / 國會交易追蹤、無漲跌幅限制之波動停損計算，預設對接 `trader-broker` Paper Trading 檢查。
* **台股（TW）**：自動補齊 `.TW` / `.TWO` 後綴，額外納入 **三大法人（外資/投信/自營商）籌碼**、**月營收 YoY** 與 **10% 漲跌幅限制** 的風控約束，避免套用美股無漲跌幅的止損假設。

---

## 目錄結構

```text
us-tw-stock-agy/
├── README.md
├── .agents/
│   └── skills/
│       └── us-tw-stock-research/
│           └── SKILL.md                 # AGY Skill 契約（自動探索載入）
├── workflows/
│   └── us_tw_analysis_workflow.py       # AGY run_workflow 多模型平行/管線編排腳本
└── remote_agent_runner.py               # Antigravity Python SDK 遠端/排程觸發入口
```
