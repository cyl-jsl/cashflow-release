import type { Income } from '../api/types'

function parseISODate(s: string): Date {
  const [y, m, d] = s.split('-').map(Number)
  return new Date(y, m - 1, d)
}

function toISODate(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function daysInMonth(year: number, month0: number): number {
  return new Date(year, month0 + 1, 0).getDate()
}

function addMonths(d: Date, months: number): Date {
  const targetYear = d.getFullYear() + Math.floor((d.getMonth() + months) / 12)
  const targetMonth = ((d.getMonth() + months) % 12 + 12) % 12
  const day = Math.min(d.getDate(), daysInMonth(targetYear, targetMonth))
  return new Date(targetYear, targetMonth, day)
}

function advanceDate(current: Date, frequency: Income['frequency']): Date | null {
  if (frequency === 'once') return null
  if (frequency === 'biweekly') {
    const next = new Date(current)
    next.setDate(next.getDate() + 14)
    return next
  }
  if (frequency === 'monthly') return addMonths(current, 1)
  if (frequency === 'quarterly') return addMonths(current, 3)
  if (frequency === 'yearly') return addMonths(current, 12)
  return null
}

export interface PaydayInfo {
  date: string
  isPast: boolean
}

/**
 * 從 income.start_date 起依 frequency 推進，回傳「最近一個過去發薪日 + 未來 (count-1) 個」。
 * 若沒有過去發薪日（start_date 在未來），則回傳前 count 個未來發薪日。
 * end_date 之後的不回傳。
 */
export function getRecentPaydays(income: Income, count = 6): PaydayInfo[] {
  if (income.frequency === 'once') return []

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const endLimit = income.end_date ? parseISODate(income.end_date) : null

  const all: Date[] = []
  let cursor: Date | null = parseISODate(income.start_date)
  const maxIter = 600
  let lastPast: Date | null = null
  let firstFutureIdx = -1

  for (let i = 0; i < maxIter && cursor; i++) {
    if (endLimit && cursor > endLimit) break
    all.push(cursor)
    if (cursor <= today) {
      lastPast = cursor
    } else if (firstFutureIdx === -1) {
      firstFutureIdx = all.length - 1
    }
    if (firstFutureIdx !== -1 && all.length - firstFutureIdx >= count) break
    cursor = advanceDate(cursor, income.frequency)
  }

  const result: PaydayInfo[] = []
  if (lastPast) {
    result.push({ date: toISODate(lastPast), isPast: true })
  }
  const startFuture = firstFutureIdx === -1 ? all.length : firstFutureIdx
  for (let i = startFuture; i < all.length && result.length < count; i++) {
    result.push({ date: toISODate(all[i]), isPast: false })
  }
  return result
}
