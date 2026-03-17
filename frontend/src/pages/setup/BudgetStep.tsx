import { useState } from 'react'
import { apiFetch } from '../../api/client'

export default function BudgetStep({ onNext, onPrev }: { onNext: () => void; onPrev: () => void }) {
  const [amount, setAmount] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const handleSave = async () => {
    const parsed = parseFloat(amount)
    if (!parsed || parsed <= 0) {
      onNext()  // 允許跳過
      return
    }
    setSaving(true)
    setError('')
    try {
      const today = new Date()
      const thisMonth1st = new Date(today.getFullYear(), today.getMonth(), 1)
      const startDate = thisMonth1st.toISOString().split('T')[0]
      await apiFetch('/obligations', {
        method: 'POST',
        body: JSON.stringify({
          name: '現金生活費',
          type: 'budget',
          amount: parsed,
          frequency: 'monthly',
          start_date: startDate,
          next_due_date: startDate,
        }),
      })
      onNext()
    } catch (e: any) {
      setError(e.message || '儲存失敗')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">步驟 5：每月生活費預算</h2>
      <p className="text-gray-600 text-sm">
        估算每月<strong>不用信用卡</strong>的現金支出（早餐、市場、停車費等）。
        <br />信用卡消費會由帳單獨立計算，不需包含在這裡。
      </p>

      <div className="max-w-xs">
        <label className="text-sm text-gray-600">每月預估金額（元）</label>
        <input
          type="number"
          className="w-full border rounded px-3 py-2 text-lg"
          placeholder="8000"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
        />
      </div>

      {error && <p className="text-red-600 text-sm">{error}</p>}

      <div className="flex justify-between pt-4">
        <button onClick={onPrev} className="text-gray-500 hover:text-gray-700">上一步</button>
        <button onClick={handleSave} disabled={saving} className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50">
          {saving ? '儲存中...' : amount.trim() ? '下一步' : '跳過'}
        </button>
      </div>
    </div>
  )
}
