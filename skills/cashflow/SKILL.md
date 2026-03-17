---
name: cashflow
description: >-
  Use when the user asks about personal finances, account balances,
  available funds, upcoming bills, credit card bills, fixed expenses,
  savings goals, spending feasibility, or invokes /cashflow.
  Manages a local cashflow API at localhost:8000.
---

# Cashflow

## Overview

Single skill entry point for personal cashflow management. Agent calls
`http://localhost:8000/api/v1/...` via curl. No MCP server needed.

**Core principles:**
- Parse natural language intent → map to API endpoint
- All write operations require user confirmation (see HARD-GATE below)
- Amounts displayed as integer TWD (round API floats)
- Auto-detect and start backend if not running

**Not applicable:**
- Enterprise finance / accounting questions
- Modifying cashflow system source code
- Changing API schema or behavior

## Execution Flow

```
User input (natural language or /cashflow + text)
    |
1. Health Check
   curl -sf http://localhost:8000/api/v1/health
   | fail -> auto-start backend (see below)
   | success
   First query per session -> POST /system/advance-cycles (no confirmation)
   If advanced > 0 -> append notice: (已自動推進 N 筆收入/義務的週期)
    |
2. Parse intent -> map to API endpoint (see intent tables below)
    |
3. Read operation -> call API -> format response (see response-formats.md)
   Write operation -> show confirmation -> wait for user -> call API -> report
```

### Backend Auto-Start

1. `curl -sf http://localhost:8000/api/v1/health` → success = running
2. If fail → Bash `run_in_background`:
   `cd <project_root>/backend && source .venv/bin/activate && uvicorn app.main:app --port 8000`
3. Wait 3s, retry health check, max 3 attempts
4. All retries fail → run `lsof -i :8000` to diagnose port conflict, report findings to user

## Confirmation Mechanism

<HARD-GATE>
所有寫入操作（POST/PUT/PATCH/DELETE，除「例外」列表中的 endpoint 外）必須在執行前列出操作摘要並等待使用者確認。未經確認就執行寫入操作是違規行為，沒有例外。
</HARD-GATE>

### Exceptions (no confirmation needed)

- All GET requests
- `POST /planning/can-i-spend` — idempotent calculation
- `POST /planning/savings-goal` — idempotent calculation
- `POST /forecast/simulate` — idempotent simulation
- `POST /system/advance-cycles` — low-risk system maintenance

### Confirmation Format

```
即將執行：{操作描述}
  {field1}：{value1}
  {field2}：{value2}

確認執行？
```

### Delete Safety

Before any DELETE: call `GET /system/backup` to save database.
`curl -o <project_root>/data/cashflow-backup-YYYY-MM-DD-HHmmss.db http://localhost:8000/api/v1/system/backup`
Warn user: `[!] 此操作不可復原，將先自動備份資料庫`
Note: Use timestamp in filename (e.g. `2026-03-15-143022`) to avoid same-day overwrites.

### Batch Confirmation

During batch initial setup or multi-item operations: collect all data first, then show one combined confirmation, then execute all at once. Avoid per-item confirmation fatigue.

## Intent Mapping

### Query Operations (no confirmation)

| User Intent | API Call | Response Focus |
|---|---|---|
| 「總覽」「目前狀況」「儀表板」 | GET /dashboard/summary | available amount, balances, upcoming 7-day dues, stale warnings |
| 「我能動多少錢」「到月底剩多少」「還有多少錢」 | GET /forecast/available | available amount + breakdown |
| 「到發薪日還剩多少」 | GET /forecast/available?period_type=next_payday | available amount |
| 「未來 N 天能動多少」 | GET /forecast/available?period_type=days&period_value=N | available amount |
| 「列出帳戶」「帳戶餘額」 | GET /accounts | account list + balances |
| 「列出收入」 | GET /incomes | income list |
| 「列出義務」「固定支出」「每月固定支出多少」 | GET /obligations or GET /obligations?type=fixed | obligation list |
| 「房租多少」「XX 多少錢」 | GET /obligations → filter by name | single obligation amount |
| 「列出信用卡」 | GET /credit-cards | credit card list |
| 「列出帳單」「X 月帳單」 | GET /credit-card-bills?billing_year=YYYY&billing_month=X | bill list (year defaults to current) |
| 「備份資料庫」 | GET /system/backup | curl -o to save file, report path |
| 「未來走勢」「下個月會怎樣」 | GET /forecast/timeline | timeline data (dates + relative days) |
| 「我能花 X 嗎」 | POST /planning/can-i-spend | feasibility result (suggest alternative if not feasible) |
| 「每月存 X，多久到 Y」 | POST /planning/savings-goal | savings analysis (suggest adjustment if not feasible) |
| 「如果收入增加 X / 支出減少 Y」 | POST /forecast/simulate | simulation comparison. Note: 「支出減少 2000」→ `monthly_expense_change: -2000` (negative) |
| 「列出交易」 | GET /transactions | imported transaction list |

### Write Operations (confirmation required)

| User Intent | API Call | Confirmation Points |
|---|---|---|
| 「新增帳戶 XX」 | POST /accounts | name, type, balance |
| 「更新 XX 餘額為 YY」 | PUT /accounts/{id} | account name, new balance |
| 「批次更新餘額」 | PATCH /accounts/batch-update-balances | each account name + new balance |
| 「刪除帳戶 XX」 | DELETE /accounts/{id} | account name (warn irreversible) |
| 「新增收入 XX」 | POST /incomes | name, amount, frequency, start_date |
| 「修改薪水為 XX」「調薪了」 | PUT /incomes/{id} | field + new value |
| 「刪除收入 XX」 | DELETE /incomes/{id} | income name |
| 「新增義務/支出 XX」 | POST /obligations | name, type, amount, frequency |
| 「修改 XX 金額為 YY」 | PUT /obligations/{id} | field + new value |
| 「刪除義務 XX」 | DELETE /obligations/{id} | obligation name (installment cascades) |
| 「新增信用卡 XX」 | POST /credit-cards | name, billing_day, due_day |
| 「刪除信用卡 XX」 | DELETE /credit-cards/{id} | card name. Before confirming: query bills + installments for this card, show cascade impact: 「將同時刪除 N 筆帳單、M 筆分期」 |
| 「新增帳單」 | POST /credit-card-bills | card, month, general_spending, due_date |
| 「標記帳單已繳」「XX 帳單繳了」「卡費繳了」「帳單付了」 | PUT /credit-card-bills/{id} | bill name + amount. Pre-check: GET bill first; if already is_paid=true, tell user「此帳單已標記為已繳」and abort. (see Post-Payment Linkage) |
| 「載入範例資料」 | POST /system/load-sample-data | confirm: about to load sample data |
| 「匯入交易」 | POST /transactions/import | filename, linked account/card |
| 「刪除交易批次」 | DELETE /transactions?source_file=X | source_file + count |

### Shorthand Recognition

| User Input | Interpretation | Operation |
|---|---|---|
| 「中信 75000」 | Update 中信 balance to 75000 | PUT /accounts/{id} |
| 「中信 75000，郵局 28000」 | Batch update balances | PATCH /accounts/batch-update-balances |
| 「中信 75000，郵局 28000，玉山卡帳單繳了」 | Batch update + mark bill paid | Multi-step, one confirmation |

**Rule:** When user provides only「account name + number」, default interpretation = update balance.

### Number Parsing

When parsing user-provided amounts:
- Strip thousand separators: `75,000` → `75000`
- Convert Chinese units: `7.5萬` → `75000`, `3千` → `3000`, `6k` → `6000`
- Always show parsed amount in confirmation for user to verify.

### Semantic Ambiguity

| User Says | Agent Response |
|---|---|
| 「房租繳了」「繳了房租」 | Guide to update account balance (obligations have no "paid" concept, only bills do) |
| 「薪水入帳了」 | Guide to update account balance |
| 「幫我記一下 XX」 | Clarify: add obligation, update balance, or add transaction? |
| 「這個月花了多少」 | Explain: this system doesn't do bookkeeping, but can show obligation + bill totals |
| 「卡費繳了」「帳單付了」（未指定卡別） | Query current month unpaid bills; if 1 → confirm that bill; if multiple → list for user to choose |
| 「自動扣款了」「已扣繳」 | Clarify: credit card bill auto-debit, or other fixed expense deducted? |
| 「多少錢」（no subject） | Clarify: available amount, account balance, or a specific obligation? |
| 「更新」「刪掉」「新增」（no object） | List available resource types for user to choose |
| 「不繳 XX 會怎樣」 | Use POST /forecast/simulate with that obligation's amount as monthly_expense_change (negative) |
| 「取消訂閱 XX」「退訂 XX」 | Map to DELETE /obligations/{id} after resolving XX |
| 「下週有保險理賠 X 萬入帳」 | POST /incomes — frequency=once, start_date=入帳日 |
| 「下個月要包紅包 X 元」 | POST /obligations — type=fixed, frequency=once, start_date=支出日 |
| 「有一筆臨時收入」 | 確認金額與日期，POST /incomes frequency=once |

### Composite Query Operations (multi-API reasoning, no confirmation)

| User Intent | Playbook |
|---|---|
| 「要領多少錢」「提多少現金」 | 現金提領計算 |
| 「可以花多少」「消費額度」「信用卡可以刷多少」 | 期間可用資金規劃 |
| 「旅遊預算」「出國可以花多少」 | 期間可用資金規劃（特殊事件模式） |
| 「分期還要多久」「什麼時候比較寬裕」 | 期間可用資金規劃（附分期到期時間表） |
| 「分析帳單」「對帳」「核對帳單」+ 附檔 | 信用卡帳單對帳 |

### Post-Payment Linkage

After marking a credit card bill as paid, MUST proactively handle account linkage:

若 CreditCard.payment_method 值非 null：
  依信用卡設定帶入帳戶，以詢問語氣確認。

若 CreditCard.payment_method 值為 null：
  依 CLAUDE.md 偏好帶入帳戶，以詢問語氣確認：

```
帳單 {amount} 元已標記已繳。
依您的習慣，通常以現金繳納。要從「現金」帳戶扣除嗎？
  現金：目前 {current} → 扣除 {bill_amount} → {new_balance} 元
```

## ID Resolution

Users refer to resources by name, not ID. Before write operations, query the list endpoint to resolve ID.

**Fuzzy match priority:** exact match > prefix match > contains match. Case-insensitive.
**Multiple matches (>= 2):** MUST list candidates for user to choose. Never auto-select.
**Cross-resource ambiguity:** When user doesn't specify resource type (e.g. 「刪除中信」), check accounts + credit-cards + obligations. If matches span multiple types, list all with type labels for user to choose.
**No match (resource count <= 10):** Show full list: 「找不到『國泰』，目前帳戶有：中信薪轉、郵局儲蓄、現金。請問是哪一個？」
**No match (resource count > 10):** Show top 5 closest matches + prompt user to use「列出全部」for complete list.

## User Preferences

以下為使用者已確認的偏好，Agent 必須遵守，不可自行假設。
詳細內容見專案 CLAUDE.md。此處僅列 Agent 行為規範：

### 支付方式判斷優先序
1. 系統欄位（payment_method）值非 null → 依欄位值
2. CLAUDE.md 記載的使用者偏好 → 依偏好值，以詢問語氣確認
3. 以上皆無 → 直接詢問使用者

### Agent 禁止假設清單
- 不可假設任何支出的支付方式（現金/轉帳/自動扣款）
- 不可假設信用卡帳單是自動扣款
- 不可假設收入入帳到哪個帳戶

## Business Rules

1. **Amounts:** API accepts/returns float (元). Display to user as integer (round)
2. **billing_day / due_day:** Must be 1~28. Month-end (29/30/31) → tell user to use 28
3. **Obligation installment:** type=installment requires installment details in body
4. **Unique bill:** Same card + same month = one bill. Duplicate → 409 DUPLICATE_BILL
5. **Post-bill-payment:** After marking bill paid, ask user to update account balance (see Post-Payment Linkage)
6. **Budget type:** Cash expenses only (excludes credit card). Cross-month queries deduct full month per covered month (conservative estimate, explain to user)
7. **advance-cycles:** Execute once per skill session on first query. Don't repeat within same session
8. **Delete credit card:** Cascades to all related bills and installments
9. **Delete obligation:** type=installment cascades to installment details
10. **Simulate sign convention:** 「支出減少 2000」→ `monthly_expense_change: -2000` (negative=decrease, positive=increase)
11. **Partial payment carry-forward:** When `paid_amount` < `total_amount`, backend auto-calculates revolving interest and creates/updates next month's bill with `carried_forward`. Inform user of the carry-forward amount
12. **advance-cycles installment:** Also decrements `remaining_periods` and updates `current_period_date`. When `remaining_periods` reaches 0, auto-sets obligation `end_date` (installment complete)
13. **Available amount formula:** `available = total_balance + period_income - period_obligations - period_credit_card_bills`. Bills include `installment_amount + general_spending + carried_forward`
14. **Installment excluded from forecast:** type=installment obligations are excluded from forecast calculation (amount handled via CreditCardBill.installment_amount)
15. **Batch update atomicity:** `PATCH /accounts/batch-update-balances` is all-or-nothing; if any account ID not found, entire batch fails with 404
16. **資金規劃安全期間：** 當使用者詢問「可花多少」「旅遊預算」「提領多少」等
    規劃性問題時，計算期間 = `max(使用者指定日期, next_payday)`。即使使用者只問到
    某個較近的日期，計算必須覆蓋到下一筆 frequency=monthly 收入的入帳日。
    規劃期間內的所有支出（帳單、固定支出、現金需求）都必須預留。
17. **帳單費用分類規則：** 信用卡帳單上除了「分期本金」（由 installment_amount 管理）
    和「循環利息」（由 revolving_interest 機制管理）之外的所有費用，一律歸入
    general_spending。包含但不限於：分期利息/手續費、年費、違約金、預借現金利息。
    歸類後必須告知使用者，不可靜默歸入。

## Batch Initial Setup

When user first uses the system or asks to「幫我設定好」, guide through these steps.
User can say「跳過」or「先這樣就好」to exit early at any step.

1. **Accounts** — bank, cash, investment accounts with current balances
2. **Income** — sources, amounts, frequency, dates (prompt: 薪水、年終、租金收入)
3. **Fixed expenses** — monthly obligations (prompt: 房租、保險、訂閱、勞健保自付額、房屋稅/牌照稅(yearly)、綜合所得稅(5月,yearly))
4. **Cash budget** — estimated monthly cash spending (excluding credit card)

**Mid-point checkpoint:** After steps 1-4, call `GET /dashboard/summary` to show overview. Ask user whether to continue with credit card setup.

5. **Credit cards** — card names, billing_day, due_day
6. **Active installments** — ongoing purchase/bill installments
7. **Current bills** — unpaid bills for current month

**Finish:** Call `GET /dashboard/summary` for final overview.
**Confirmation:** Each step uses batch confirmation (collect all → one confirmation → execute all).

## Composite Query Playbooks

當使用者的問題無法用單一 API 回答時，依照以下 playbook 組合數據。
Agent 透過 Intent Mapping 表判定應執行哪個 Playbook，以下各 Playbook 的觸發詞僅為參考範例。

### Playbook: 現金提領計算

**Fast-path：** 若 withdrawal-advice API 可用，呼叫 `GET /forecast/withdrawal-advice?until={安全邊界日期}`（日期由安全期間 Rule 計算）並格式化回應，跳過以下手動步驟。

手動流程（API 不可用時）：
依支付方式判斷優先序（見 User Preferences）判定各支出/收入的現金/轉帳歸屬，
分別呼叫 /accounts、/incomes、/obligations、/credit-card-bills，
計算 cash_outflows - current_cash - cash_inflows = 需提領金額。
週期性收支需展開所有到期期數。帳單僅計入 is_paid=false。

### Playbook: 期間可用資金規劃

1. 確定期間與安全邊界（安全期間 Rule）
2. GET /accounts（取得總資產）
3. GET /incomes + /obligations + /credit-card-bills（僅 is_paid=false。週期性收支需展開所有到期期數）
4. 計算總可支配 = 總資產 + 期間收入 - 期間所有支出
5. 若問特定卡額度：月收入 - 非該卡支出 = 該卡可分配額度 - 分期 = 一般消費空間
6. 若涉及特殊事件（旅遊）：從可支配中扣除安全邊界內的所有後續支出
7. 附加：列出分期到期時間表，呈現未來月份的額度成長

### Playbook: 信用卡帳單對帳

四階段流程，每階段輸出後等使用者確認再繼續：

1. **解析** — 讀取檔案，識別交易明細、帳單摘要、分期項目
2. **分類** — 按類別（餐飲/交通/訂閱/便利商店/購物/充電租借/其他）統計金額與佔比
3. **比對** — GET /credit-card-bills 和 /obligations?type=installment，比對 CSV 總額 vs 系統 total、分期金額 vs installment_amount。若系統無該月帳單，引導使用者先建立。差異依帳單費用分類 Rule 歸類。
4. **執行** — 更新 general_spending（若有差異）、清理 CSV 匯入 transactions。所有寫入遵循 HARD-GATE。

## Transaction Import

1. Verify file exists: `ls {filepath}`
2. **Duplicate check:** `GET /transactions?source_file={filename}` — if records exist, warn user and ask whether to continue or abort
3. Preview CSV headers: `head -5 {filepath}` → auto-detect column mapping (or ask user)
4. Confirm import parameters (file, columns, linked account/card)
5. Execute: `curl -X POST http://localhost:8000/api/v1/transactions/import -F "file=@{path}" -F "date_column=..." -F "amount_column=..." [-F "credit_card_id=N" | -F "account_id=N"]`

## Error Handling

| HTTP Status | Error Code | Agent Response |
|---|---|---|
| 404 | NOT_FOUND | 「找不到 {resource}，請確認名稱」+ candidate list |
| 409 | DUPLICATE_BILL | 「該卡該月帳單已存在，是否要更新？」 |
| 422 | VALIDATION_ERROR | Translate error to user-friendly Chinese |
| 400 | INVALID_PERIOD | 「期間參數格式有誤，請指定日期或使用 end_of_month / next_payday / days:N」 |
| 400 | NO_MONTHLY_INCOME | 「尚未設定月薪收入，無法計算到發薪日。請先新增收入」 |
| 400 | VALIDATION_ERROR | Bill installment: 「此帳單已繳清或已轉分期」or「來源帳單與指定信用卡不一致」 |
| 422 | VALIDATION_ERROR | Transaction import CSV/Excel parse error → tell user to check file format |
| 500 | — | 「後端發生內部錯誤，請稍後再試。要我查看後端 log 嗎？」 |
| Connection fail | — | Auto-start backend. If still fails → tell user to check manually |

## Reference Files

For API endpoint details (request body, response schema): Read [api-reference.md](api-reference.md)
For response formatting templates: Read [response-formats.md](response-formats.md)
