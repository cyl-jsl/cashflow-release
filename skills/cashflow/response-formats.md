# Cashflow Response Formats

API responses should be transformed into human-readable Chinese summaries, not raw JSON. Add relative days to dates for intuitive understanding.

When the user is asking for reassurance-oriented budget guidance, do not lead with raw balance math. Lead with a single safe-to-use number, then separate book balance, reserved funds, and safety buffer.

---

## 1. Dashboard Summary

```
可動用金額：{available_amount} 元（到 {until_date} {description}，{relative_days} 天後）
帳戶總餘額：{total_balance} 元

帳戶：
  {account_name}：{balance} 元
  {account_name}：{balance} 元

近期到期（7 天內）：
  {due_date}（{relative_days} 天後）{name}：{amount} 元（{paid_status}）

[!] 餘額過期：{account_name}（{days_since_update} 天未更新）
```

## 2. Available Amount

### 2A. Safety-First Format

Use this format for queries such as「這個月安全額度是多少」「我現在真正可花多少」「這筆錢能不能動」.

Rules:

- First line must answer with one number: `safe_available_amount`
- Always state the assumed safety period
- Always separate `帳面總餘額`, `不能動的預留`, and `安全邊界`
- If the user has a recurring spending habit reserve, show it as `消費慣例預留`
- If the user has requested a safety buffer, show it separately even when it is 0
- If useful, add the lowest balance point in the period so the user knows where the real pressure is

```
本月安全額度：{safe_available_amount} 元
前提：從今天到 {until_date}（{period_description}）已先扣掉必要支出、已知帳單／分期、消費慣例預留，並保留安全邊界 {safety_buffer} 元。

三個關鍵數字：
  帳面總餘額：{total_balance} 元
  不能動的預留：{reserved_total} 元
  真正可自由動用：{safe_available_amount} 元

預留明細：
  必要支出：{required_expenses} 元
  已知信用卡帳單／分期：{credit_card_reserve} 元
  消費慣例預留：{habit_spending_reserve} 元
  安全邊界：{safety_buffer} 元

風險提示：
  最低水位：{lowest_balance} 元（{lowest_date}）
```

### 2B. Raw Period Breakdown

Use this format only when the user explicitly wants the raw period math.

```
到{period_description}（{until_date}，{relative_days} 天後）可動用：{available_amount} 元
  帳戶總額：{total_balance} 元
  + 期間收入：{period_income} 元
  − 義務支出：{period_obligations} 元（budget 為整月保守估計）
  − 信用卡帳單：{period_credit_card_bills} 元
```

## 3. Can-I-Spend — Feasible

```
花費 {amount} 元 → 可行
  花費前可動用：{available_before} 元
  花費後可動用：{available_after} 元
  計算期間：{from} ~ {until}
```

## 4. Can-I-Spend — Not Feasible

```
花費 {amount} 元 → 不可行
  花費前可動用：{available_before} 元
  花費後可動用：{available_after} 元（不足 {shortfall} 元）
  建議：{alternative_suggestion}
```

## 5. Savings Goal

```
目標：{target_amount} 元，每月存 {monthly_saving} 元
  每月可存餘裕：{monthly_surplus} 元 → {feasibility}
  預計 {months_needed} 個月後達成（{projected_date}）
```

## 6. Simulation Comparison

```
模擬：月收入 {income_change} 元、月支出 {expense_change} 元，共 {months} 個月

  月份       原始餘額      模擬餘額      差異
  {date}    {baseline}      {simulated}    {diff}
  {date}    {baseline}      {simulated}    {diff}
  ...
```

## 7. Write Success

```
{resource_type}「{name}」已{action}（ID: {id}）
  {key_field}：{value}
```

## 8. Cycle Advance Notice

Append to other responses when advance count > 0:

```
（已自動推進 {income_count} 筆收入、{obligation_count} 筆義務的週期）
```

## 9. Income Adjustment

### 9A. Upsert Actual

Use after `POST /incomes/{id}/actuals`. Always show both the actual and delta vs base.

```
{income_name} {effective_date} 實領 {actual_amount} 元已記錄
  基準金額：{base_amount} 元
  本次差異：{delta_amount}（{+/-}）
  備註：{note 或「無」}
```

If delta_amount is non-trivial (例：>= 5% of base 或 user has a preference), proactively note 對 forecast 的影響：
「這次少領 X 元，會反映到 {effective_date} 之後的可用資金預估。」

### 9B. List Adjustments

Use after `GET /incomes/{id}/adjustments`. Sort by effective_date.

```
{income_name} 已記錄 {count} 筆實領：
  {effective_date}    實領 {actual_amount}    差 {±delta}    {note 或 ''}
  {effective_date}    實領 {actual_amount}    差 {±delta}    {note 或 ''}
  ...
未記錄的發薪日皆以基準 {base_amount} 元計算。
```

### 9C. Remove Adjustment

Use after `DELETE /income-adjustments/{id}`. Tell user the row is gone, future forecast will fall back to base.

```
{income_name} {effective_date} 的 actual 已移除，回到使用基準 {base_amount} 元。
```
