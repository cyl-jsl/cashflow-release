import { useEffect, useState } from 'react'
import type { Income, IncomeAdjustment } from '../api/types'
import {
  useUpsertIncomeActual,
  useDeleteIncomeAdjustment,
} from '../hooks/useIncomeAdjustments'
import { formatCurrency } from '../utils/format'

export interface IncomeActualModalProps {
  income: Income
  effectiveDate: string
  existing: IncomeAdjustment | null
  onClose: () => void
}

export default function IncomeActualModal({
  income,
  effectiveDate,
  existing,
  onClose,
}: IncomeActualModalProps) {
  const [actualAmount, setActualAmount] = useState(
    existing ? existing.actual_amount.toString() : income.amount.toString(),
  )
  const [note, setNote] = useState(existing?.note ?? '')
  const [error, setError] = useState<string | null>(null)

  const upsert = useUpsertIncomeActual(income.id)
  const remove = useDeleteIncomeAdjustment(income.id)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const parsed = parseFloat(actualAmount)
  const valid = Number.isFinite(parsed) && parsed > 0
  const delta = valid ? parsed - income.amount : 0

  const handleSave = () => {
    if (!valid) {
      setError('請輸入大於 0 的金額')
      return
    }
    setError(null)
    upsert.mutate(
      {
        effective_date: effectiveDate,
        actual_amount: parsed,
        note: note.trim() || null,
      },
      {
        onSuccess: () => onClose(),
        onError: (e: Error) => setError(e.message),
      },
    )
  }

  const handleRemove = () => {
    if (!existing) return
    if (!confirm('移除此筆 actual，回到使用基準金額？')) return
    remove.mutate(existing.id, {
      onSuccess: () => onClose(),
      onError: (e: Error) => setError(e.message),
    })
  }

  const pending = upsert.isPending || remove.isPending

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl shadow-lg w-full max-w-md mx-4 p-6 space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div>
          <h2 className="text-lg font-semibold">編輯實領金額</h2>
          <p className="text-sm text-gray-500 mt-1">
            {income.name} · {effectiveDate}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            基準金額 {formatCurrency(income.amount)}
          </p>
        </div>

        <div className="space-y-2">
          <label className="block text-sm text-gray-700">實領金額</label>
          <input
            className="w-full border rounded px-3 py-2"
            type="number"
            step="1"
            value={actualAmount}
            onChange={(e) => setActualAmount(e.target.value)}
            autoFocus
          />
          {valid && delta !== 0 && (
            <p className={`text-xs ${delta > 0 ? 'text-emerald-600' : 'text-amber-600'}`}>
              {delta > 0 ? '+' : ''}
              {formatCurrency(delta)} 相對基準
            </p>
          )}
        </div>

        <div className="space-y-2">
          <label className="block text-sm text-gray-700">備註（選填）</label>
          <input
            className="w-full border rounded px-3 py-2"
            placeholder="例：年終獎金、績效加給"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex justify-between items-center pt-2">
          <div>
            {existing && (
              <button
                className="text-sm text-red-600 hover:underline disabled:opacity-50"
                onClick={handleRemove}
                disabled={pending}
              >
                移除 actual
              </button>
            )}
          </div>
          <div className="flex gap-2">
            <button
              className="px-4 py-2 rounded border disabled:opacity-50"
              onClick={onClose}
              disabled={pending}
            >
              取消
            </button>
            <button
              className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
              onClick={handleSave}
              disabled={pending || !valid}
            >
              {pending ? '處理中...' : '儲存'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
