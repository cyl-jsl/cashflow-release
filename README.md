# Cashflow

個人現金流管理系統 — 追蹤帳戶餘額、固定收支、信用卡帳單與分期付款，預測未來可動用金額。

## Features

- 帳戶餘額管理（銀行、現金、投資）
- 週期性收入 / 固定支出追蹤
- 信用卡帳單管理（含分期付款、循環利息試算）
- 現金流預測（到月底 / 到發薪日 / 自訂天數）
- 消費可行性評估（「我能花 X 元嗎？」）
- 儲蓄目標規劃
- 收支模擬（如果收入增加 / 支出減少會怎樣）
- CSV / Excel 交易匯入

## Tech Stack

- **Backend:** Python 3 · FastAPI · SQLAlchemy · Alembic · SQLite
- **Frontend:** React 19 · TypeScript · Vite · Tailwind CSS · Recharts · TanStack Query

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --port 8000
```

API 文件：啟動後瀏覽 `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

開啟 `http://localhost:5173`

### Sample Data

啟動 backend 後，載入範例資料：

```bash
curl -X POST http://localhost:8000/api/v1/system/load-sample-data
```

## AI Agent Integration

`skills/cashflow/` 包含 Claude Code agent skill 定義，讓 AI 助手能透過自然語言操作此系統的 REST API。詳見該目錄下的 SKILL.md。

## License

[MIT](LICENSE)
