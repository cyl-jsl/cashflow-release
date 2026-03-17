export interface Account {
  id: number
  name: string
  type: 'bank' | 'cash' | 'investment'
  balance: number
  balance_updated_at: string
  currency: string
  note: string | null
}

export interface Income {
  id: number
  name: string
  amount: number
  frequency: 'monthly' | 'biweekly' | 'quarterly' | 'yearly' | 'once'
  start_date: string
  end_date: string | null
  next_date: string
  note: string | null
}

export interface Obligation {
  id: number
  name: string
  type: 'fixed' | 'installment' | 'budget'
  amount: number
  frequency: 'monthly' | 'biweekly' | 'quarterly' | 'yearly' | 'once'
  start_date: string
  end_date: string | null
  next_due_date: string
  note: string | null
}

export interface ForecastAvailable {
  total_balance: number
  period_income: number
  period_obligations: number
  period_credit_card_bills: number
  available_amount: number
  period: { from: string; until: string }
}

export interface CreditCard {
  id: number
  name: string
  billing_day: number
  due_day: number
  credit_limit: number | null
  note: string | null
  revolving_interest_rate: number | null
}

export interface InstallmentDetail {
  id: number
  obligation_id: number
  credit_card_id: number
  installment_type: string
  total_amount: number
  monthly_amount: number
  total_periods: number
  remaining_periods: number
  interest_rate: number | null
  fee: number | null
  current_period_date: string
  source_bill_id: number | null
  effective_from_period: string | null
}

export interface CreditCardBill {
  id: number
  credit_card_id: number
  billing_year: number
  billing_month: number
  due_date: string
  installment_amount: number
  general_spending: number
  total_amount: number
  is_paid: boolean
  paid_amount: number | null
  carried_forward: number
}

export interface UpcomingDue {
  type: 'credit_card_bill' | 'obligation'
  name: string
  amount: number
  due_date: string
  is_paid?: boolean
}

export interface StaleAccount {
  id: number
  name: string
  days_since_update: number
}

export interface AccountSummary {
  id: number
  name: string
  balance: number
  balance_updated_at: string
  is_stale: boolean
}

export interface DashboardSummary {
  total_balance: number
  available_amount: number
  available_period: { from: string; until: string }
  accounts: AccountSummary[]
  upcoming_dues: UpcomingDue[]
  stale_accounts: StaleAccount[]
}

export interface TimelinePoint {
  date: string
  balance: number
  income_total: number
  obligation_total: number
  credit_card_total: number
  note: string | null
}

export interface TimelineData {
  timeline: TimelinePoint[]
  granularity: string
  months: number
}

export interface CanISpendRequest {
  amount: number
  date?: string
}

export interface CanISpendResponse {
  available_before: number
  available_after: number
  period: { from: string; until: string }
  is_feasible: boolean
  summary: string
}

export interface SavingsGoalRequest {
  target_amount: number
  monthly_saving?: number
  target_date?: string
}

export interface SimulateRequest {
  monthly_income_change: number
  monthly_expense_change: number
  months: number
}

export interface SimulateResponse {
  baseline: TimelinePoint[]
  simulated: TimelinePoint[]
  months: number
}

export interface SavingsGoalResponse {
  monthly_surplus: number
  monthly_needed: number | null
  months_to_target: number | null
  months_needed: number | null
  projected_date: string | null
  target_date: string | null
  is_feasible: boolean
  summary: string
}

export interface Transaction {
  id: number
  date: string
  description: string
  amount: number
  credit_card_id: number | null
  account_id: number | null
  category: string | null
  source_file: string
  imported_at: string
}

export interface ImportResponse {
  transactions_created: number
  total_spending: number
  source_file: string
  credit_card_id: number | null
}
