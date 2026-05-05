import { useMemo, useState } from 'react'
import type { Income, IncomeAdjustment } from '../api/types'
import { useIncomeAdjustments } from '../hooks/useIncomeAdjustments'
import { getRecentPaydays } from '../utils/schedule'
import { formatCurrency } from '../utils/format'
import IncomeActualModal from './IncomeActualModal'

interface Props {
  income: Income
}

export default function IncomeActualsList({ income }: Props) {
  const [editingDate, setEditingDate] = useState<string | null>(null)
  const { data: adjustments, isLoading } = useIncomeAdjustments(income.id)

  const paydays = useMemo(() => getRecentPaydays(income, 6), [income])

  const adjustmentByDate = useMemo(() => {
    const m = new Map<string, IncomeAdjustment>()
    adjustments?.forEach((a) => m.set(a.effective_date, a))
    return m
  }, [adjustments])

  if (income.frequency === 'once' || paydays.length === 0) return null

  const editingAdjustment = editingDate ? adjustmentByDate.get(editingDate) ?? null : null

  return (
    <div className="mt-3 border-t pt-3">
      <p className="text-xs text-gray-500 mb-2">近期發薪日</p>
      {isLoading ? (
        <div className="animate-pulse h-20 bg-gray-100 rounded" />
      ) : (
        <ul className="space-y-1">
          {paydays.map(({ date, isPast }) => {
            const adj = adjustmentByDate.get(date)
            return (
              <li
                key={date}
                className={`flex items-center justify-between text-sm rounded px-2 py-1.5 ${
                  isPast ? 'bg-gray-50' : ''
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-gray-700 tabular-nums shrink-0">{date}</span>
                  {adj ? (
                    <>
                      <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-1.5 py-0.5 text-xs shrink-0">
                        ✓ 已確認
                      </span>
                      <span className="text-gray-900 tabular-nums shrink-0">
                        {formatCurrency(adj.actual_amount)}
                      </span>
                      {adj.delta_amount !== 0 && (
                        <span
                          className={`text-xs tabular-nums shrink-0 ${
                            adj.delta_amount > 0 ? 'text-emerald-600' : 'text-amber-600'
                          }`}
                        >
                          ({adj.delta_amount > 0 ? '+' : ''}
                          {formatCurrency(adj.delta_amount)})
                        </span>
                      )}
                      {adj.note && (
                        <span className="text-xs text-gray-500 truncate">· {adj.note}</span>
                      )}
                    </>
                  ) : (
                    <span className="text-gray-500 text-xs">
                      使用基準 {formatCurrency(income.amount)}
                    </span>
                  )}
                </div>
                <button
                  className="text-xs text-indigo-600 hover:underline shrink-0 ml-2"
                  onClick={() => setEditingDate(date)}
                >
                  編輯
                </button>
              </li>
            )
          })}
        </ul>
      )}

      {editingDate && (
        <IncomeActualModal
          income={income}
          effectiveDate={editingDate}
          existing={editingAdjustment}
          onClose={() => setEditingDate(null)}
        />
      )}
    </div>
  )
}
