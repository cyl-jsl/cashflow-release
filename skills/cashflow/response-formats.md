# Cashflow Response Formats

API responses should be transformed into human-readable Chinese summaries, not raw JSON. Add relative days to dates for intuitive understanding.

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
