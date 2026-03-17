# Cashflow API Reference

## Common Conventions

- **Base URL:** `http://localhost:8000/api/v1`
- **Success response:** `{ "data": ..., "meta": { "timestamp": "..." } }`
- **Error response:** `{ "error": { "code": "...", "message": "..." } }`
- **Content-Type:** `application/json`
- **Amount unit:** 元 (float). Internal storage is 分 (int), API auto-converts

## Enum Values

**Frequency:** `monthly` | `biweekly` | `quarterly` | `yearly` | `once`

**AccountType:** `bank` | `cash` | `investment`

**ObligationType:**
- `fixed` — fixed expenses (rent, insurance, subscriptions, loan payments)
- `installment` — credit card purchase installments (excluded from forecast, amount handled by CreditCardBill)
- `budget` — estimated cash living expenses (excludes credit card spending)

**PeriodType:** `end_of_month` | `next_payday` | `days`

**InstallmentType:** `purchase` (consumer installment) | `bill` (bill installment)

---

## System

### GET /health

Health check (defined in main.py, not system router).

```bash
curl -sf http://localhost:8000/api/v1/health
```

**Response:** `{"status": "ok"}`

### POST /system/advance-cycles

Advance all overdue Income/Obligation cycles. No request body.

```bash
curl -X POST http://localhost:8000/api/v1/system/advance-cycles
```

**Response:**
```json
{
  "data": {
    "incomes_advanced": 2,
    "obligations_advanced": 3
  }
}
```

### GET /system/backup

Download SQLite database backup. Returns `application/octet-stream` binary (NOT JSON).

```bash
curl -o <project_root>/data/cashflow-backup-YYYY-MM-DD.db \
  http://localhost:8000/api/v1/system/backup
```

### POST /system/load-sample-data

Load sample data (3 accounts + 1 income + 4 obligations). If data exists: `{"data": {"message": "資料已存在，跳過載入"}}`.

```bash
curl -X POST http://localhost:8000/api/v1/system/load-sample-data
```

**Response:**
```json
{ "data": { "accounts_created": 3, "incomes_created": 1, "obligations_created": 4 } }
```

---

## Dashboard

### GET /dashboard/summary

Returns all dashboard data. Default period until next payday. `upcoming_dues` includes only items due within 7 days.

```bash
curl -s http://localhost:8000/api/v1/dashboard/summary
```

**Response:**
```json
{
  "data": {
    "total_balance": 110000,
    "available_amount": 87500,
    "available_period": { "from": "2026-03-15", "until": "2026-04-05" },
    "accounts": [
      { "id": 1, "name": "中信薪轉", "balance": 80000, "balance_updated_at": "...", "is_stale": false }
    ],
    "upcoming_dues": [
      { "type": "credit_card_bill", "name": "玉山卡 3月帳單", "amount": 6000, "due_date": "2026-03-20", "is_paid": false }
    ],
    "stale_accounts": [
      { "id": 2, "name": "郵局", "days_since_update": 12 }
    ]
  }
}
```

---

## Accounts

### GET /accounts

```bash
curl -s http://localhost:8000/api/v1/accounts
```

**Response:**
```json
{
  "data": [
    { "id": 1, "name": "中信薪轉", "type": "bank", "balance": 80000, "balance_updated_at": "...", "currency": "TWD", "note": null, "created_at": "...", "updated_at": "..." }
  ]
}
```

### POST /accounts

**Required:** `name` (non-empty), `type` (bank | cash | investment)
**Optional:** `balance` (default 0), `currency` (default TWD), `note`

```bash
curl -X POST http://localhost:8000/api/v1/accounts \
  -H 'Content-Type: application/json' \
  -d '{"name": "中信薪轉", "type": "bank", "balance": 80000}'
```

### PUT /accounts/{id}

Partial update. All fields optional. Updating balance auto-updates `balance_updated_at`.

```bash
curl -X PUT http://localhost:8000/api/v1/accounts/1 \
  -H 'Content-Type: application/json' \
  -d '{"balance": 75000}'
```

### PATCH /accounts/batch-update-balances

```bash
curl -X PATCH http://localhost:8000/api/v1/accounts/batch-update-balances \
  -H 'Content-Type: application/json' \
  -d '{"updates": [{"id": 1, "balance": 75000}, {"id": 2, "balance": 28000}]}'
```

### DELETE /accounts/{id}

```bash
curl -X DELETE http://localhost:8000/api/v1/accounts/1
```

---

## Incomes

### GET /incomes

```bash
curl -s http://localhost:8000/api/v1/incomes
```

**Response:**
```json
{
  "data": [
    { "id": 1, "name": "薪水", "amount": 50000, "frequency": "monthly", "start_date": "2026-01-05", "end_date": null, "next_date": "2026-04-05", "note": null, "created_at": "...", "updated_at": "..." }
  ]
}
```

### POST /incomes

**Required:** `name`, `amount` (> 0), `frequency`, `start_date`
**Optional:** `end_date` (null = ongoing), `next_date` (default = start_date), `note`

```bash
curl -X POST http://localhost:8000/api/v1/incomes \
  -H 'Content-Type: application/json' \
  -d '{"name": "薪水", "amount": 50000, "frequency": "monthly", "start_date": "2026-01-05"}'
```

### PUT /incomes/{id}

Partial update. All fields optional.

```bash
curl -X PUT http://localhost:8000/api/v1/incomes/1 \
  -H 'Content-Type: application/json' \
  -d '{"amount": 55000}'
```

### DELETE /incomes/{id}

```bash
curl -X DELETE http://localhost:8000/api/v1/incomes/1
```

---

## Obligations

### GET /obligations

Optional filter: `?type=fixed`. When type=installment, response includes nested installment details.

```bash
curl -s http://localhost:8000/api/v1/obligations
curl -s http://localhost:8000/api/v1/obligations?type=fixed
```

**Response (with installment):**
```json
{
  "data": [
    {
      "id": 1, "name": "MacBook 分期", "type": "installment", "amount": 3000,
      "frequency": "monthly", "start_date": "2026-02-15", "end_date": null,
      "next_due_date": "2026-04-15", "note": null,
      "installment": {
        "id": 1, "obligation_id": 1, "credit_card_id": 1, "installment_type": "purchase",
        "total_amount": 36000, "monthly_amount": 3000, "total_periods": 12,
        "remaining_periods": 10, "interest_rate": null, "fee": null,
        "current_period_date": "2026-04-15", "source_bill_id": null,
        "effective_from_period": null, "created_at": "...", "updated_at": "..."
      },
      "created_at": "...", "updated_at": "..."
    }
  ]
}
```

### POST /obligations

**Body (fixed/budget):**

**Required:** `name`, `type` (fixed | budget), `amount`, `frequency`, `start_date`
**Optional:** `end_date`, `next_due_date`, `note`

```bash
curl -X POST http://localhost:8000/api/v1/obligations \
  -H 'Content-Type: application/json' \
  -d '{"name": "房租", "type": "fixed", "amount": 12000, "frequency": "monthly", "start_date": "2026-01-01"}'
```

**Body (installment — purchase):**

```bash
curl -X POST http://localhost:8000/api/v1/obligations \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "MacBook 分期", "type": "installment", "amount": 3000,
    "frequency": "monthly", "start_date": "2026-02-15",
    "installment": {
      "credit_card_id": 1, "total_amount": 36000, "total_periods": 12,
      "interest_rate": null, "fee": null, "installment_type": "purchase"
    }
  }'
```

**Body (installment — bill):**

```bash
curl -X POST http://localhost:8000/api/v1/obligations \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "3月帳單分期", "type": "installment", "amount": 5000,
    "frequency": "monthly", "start_date": "2026-04-15",
    "installment": {
      "credit_card_id": 1, "total_amount": 30000, "total_periods": 6,
      "installment_type": "bill", "source_bill_id": 5
    }
  }'
```

### PUT /obligations/{id}

Partial update. All fields optional.

### DELETE /obligations/{id}

Cascade deletes associated installment details.

---

## Credit Cards

### GET /credit-cards

```bash
curl -s http://localhost:8000/api/v1/credit-cards
```

**Response:**
```json
{
  "data": [
    { "id": 1, "name": "中信 LINE Pay", "billing_day": 15, "due_day": 3, "credit_limit": 100000, "note": null, "revolving_interest_rate": null, "created_at": "...", "updated_at": "..." }
  ]
}
```

### POST /credit-cards

**Required:** `name`, `billing_day` (1~28), `due_day` (1~28, can cross month)
**Optional:** `credit_limit` (元), `note`, `revolving_interest_rate` (annual rate, e.g. 0.15 = 15%)

```bash
curl -X POST http://localhost:8000/api/v1/credit-cards \
  -H 'Content-Type: application/json' \
  -d '{"name": "中信 LINE Pay", "billing_day": 15, "due_day": 3}'
```

### PUT /credit-cards/{id}

Partial update. All fields optional.

### DELETE /credit-cards/{id}

Cascade deletes all related bills and installments.

---

## Credit Card Bills

### GET /credit-card-bills

Optional filters: `?credit_card_id=1&billing_year=2026&billing_month=3`

Each bill contains:
- `installment_amount` — stored snapshot, auto-calculated on bill creation or installment changes (read-only)
- `general_spending` — user-entered general spending
- `total_amount` — installment_amount + general_spending + carried_forward
- `carried_forward` — carried forward from previous period
- `paid_amount` — actual paid amount (for partial payments)

```bash
curl -s http://localhost:8000/api/v1/credit-card-bills?billing_year=2026&billing_month=3
```

### POST /credit-card-bills

**Note:** Same card + same month = unique constraint. Duplicate → 409 DUPLICATE_BILL.

```bash
curl -X POST http://localhost:8000/api/v1/credit-card-bills \
  -H 'Content-Type: application/json' \
  -d '{
    "credit_card_id": 1, "billing_year": 2026, "billing_month": 3,
    "due_date": "2026-04-03", "general_spending": 6000, "is_paid": false
  }'
```

### PUT /credit-card-bills/{id}

**Updatable:** `general_spending`, `is_paid`, `due_date`, `paid_amount`
**NOT updatable:** `credit_card_id`, `billing_year`, `billing_month`

Mark as paid:
```bash
curl -X PUT http://localhost:8000/api/v1/credit-card-bills/1 \
  -H 'Content-Type: application/json' \
  -d '{"is_paid": true}'
```

Partial payment (triggers revolving interest carry-forward):
```bash
curl -X PUT http://localhost:8000/api/v1/credit-card-bills/1 \
  -H 'Content-Type: application/json' \
  -d '{"paid_amount": 5000}'
```

### DELETE /credit-card-bills/{id}

```bash
curl -X DELETE http://localhost:8000/api/v1/credit-card-bills/1
```

---

## Forecast

### GET /forecast/available

Available amount calculation. Query params (choose one):

| Param | Example | Description |
|---|---|---|
| `until` | `?until=2026-03-31` | Specific date |
| `period_type=end_of_month` | (default) | Until end of month |
| `period_type=next_payday` | | Until next payday |
| `period_type=days` + `period_value` | `?period_type=days&period_value=14` | Next N days |

```bash
curl -s http://localhost:8000/api/v1/forecast/available
curl -s "http://localhost:8000/api/v1/forecast/available?period_type=next_payday"
curl -s "http://localhost:8000/api/v1/forecast/available?period_type=days&period_value=14"
```

**Response:**
```json
{
  "data": {
    "total_balance": 110000,
    "period_income": 0,
    "period_obligations": 8000,
    "period_credit_card_bills": 14500,
    "available_amount": 87500,
    "period": { "from": "2026-03-15", "until": "2026-03-31" }
  }
}
```

### GET /forecast/timeline

**Query params:** `months` (1~24, default 6), `granularity` (daily | weekly | monthly, default monthly)

```bash
curl -s "http://localhost:8000/api/v1/forecast/timeline?months=6&granularity=monthly"
```

**Response:**
```json
{
  "data": {
    "timeline": [
      { "date": "2026-03-31", "balance": 87500, "income_total": 0, "obligation_total": 8000, "credit_card_total": 14500, "note": null }
    ],
    "granularity": "monthly",
    "months": 6
  }
}
```

### POST /forecast/simulate

All fields optional. `monthly_income_change` default 0, `monthly_expense_change` default 0, `months` default 6 (range 1~24).

**Sign convention:** 「支出減少 2000」→ `monthly_expense_change: -2000` (negative=decrease)

```bash
curl -X POST http://localhost:8000/api/v1/forecast/simulate \
  -H 'Content-Type: application/json' \
  -d '{"monthly_income_change": 5000, "monthly_expense_change": -2000, "months": 12}'
```

**Response:** Contains `baseline` and `simulated` arrays of timeline points.

---

## Planning

### POST /planning/can-i-spend

Idempotent query — does NOT modify data.

**Required:** `amount` (> 0)
**Optional:** `date` (default today)

```bash
curl -X POST http://localhost:8000/api/v1/planning/can-i-spend \
  -H 'Content-Type: application/json' \
  -d '{"amount": 3000}'
```

**Response:**
```json
{
  "data": {
    "available_before": 87500,
    "available_after": 84500,
    "period": { "from": "2026-03-15", "until": "2026-03-31" },
    "is_feasible": true,
    "summary": "花費 3,000 元後，到月底還有 84,500 元可動用，可行。"
  }
}
```

### POST /planning/savings-goal

Must provide `monthly_saving` OR `target_date` (mutually exclusive).

**Body (given monthly saving):**
```bash
curl -X POST http://localhost:8000/api/v1/planning/savings-goal \
  -H 'Content-Type: application/json' \
  -d '{"target_amount": 500000, "monthly_saving": 10000}'
```

**Body (given target date):**
```bash
curl -X POST http://localhost:8000/api/v1/planning/savings-goal \
  -H 'Content-Type: application/json' \
  -d '{"target_amount": 500000, "target_date": "2027-12-31"}'
```

**Response:**
```json
{
  "data": {
    "monthly_surplus": 22000,
    "monthly_needed": 23810,
    "months_to_target": null,
    "months_needed": 21,
    "projected_date": null,
    "target_date": "2027-12-31",
    "is_feasible": true,
    "summary": "..."
  }
}
```

---

## Transactions

### GET /transactions

Optional filters: `?credit_card_id=1` or `?account_id=1` or `?source_file=xxx.csv`

```bash
curl -s http://localhost:8000/api/v1/transactions
curl -s "http://localhost:8000/api/v1/transactions?credit_card_id=1"
```

**Response:**
```json
{
  "data": [
    { "id": 1, "date": "2026-03-01", "description": "午餐", "amount": 150, "credit_card_id": 1, "account_id": null, "category": null, "source_file": "march.csv", "imported_at": "..." }
  ]
}
```

### POST /transactions/import

Upload CSV/Excel file. Uses multipart/form-data.

**Form fields:**
- `file` — file (required)
- `date_column` — date column name (default "date")
- `description_column` — description column name (default "description")
- `amount_column` — amount column name (default "amount")
- `credit_card_id` — linked credit card ID (optional)
- `account_id` — linked account ID (optional)

```bash
curl -X POST http://localhost:8000/api/v1/transactions/import \
  -F "file=@/path/to/file.csv" \
  -F "date_column=日期" \
  -F "amount_column=金額" \
  -F "credit_card_id=1"
```

**Response:**
```json
{ "data": { "transactions_created": 25, "total_spending": 15000, "source_file": "march.csv", "credit_card_id": 1 } }
```

### DELETE /transactions?source_file=xxx.csv

Delete transactions by import batch. `source_file` is required.

```bash
curl -X DELETE "http://localhost:8000/api/v1/transactions?source_file=xxx.csv"
```
