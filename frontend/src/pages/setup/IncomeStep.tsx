import { useState } from 'react'
import { apiFetch } from '../../api/client'

export default function IncomeStep({ onNext, onPrev }: { onNext: () => void; onPrev: () => void }) {
  const [incomes, setIncomes] = useState<{ name: string; amount: string; frequency: string; next_date: string }[]>([
    { name: '', amount: '', frequency: 'monthly', next_date: '' },
  ])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const addRow = () => setIncomes([...incomes, { name: '', amount: '', frequency: 'monthly', next_date: '' }])
  const removeRow = (i: number) => setIncomes(incomes.filter((_, idx) => idx !== i))
  const updateRow = (i: number, field: string, value: string) => {
    const updated = [...incomes]
    updated[i] = { ...updated[i], [field]: value }
    setIncomes(updated)
  }

  const handleSave = async () => {
    const valid = incomes.filter((inc) => inc.name.trim() && inc.amount.trim() && inc.next_date)
    if (valid.length === 0) {
      onNext()  // 允許跳過
      return
    }
    setSaving(true)
    setError('')
    try {
      for (const inc of valid) {
        await apiFetch('/incomes', {
          method: 'POST',
          body: JSON.stringify({
            name: inc.name.trim(),
            amount: parseFloat(inc.amount) || 0,
            frequency: inc.frequency,
            start_date: inc.next_date,
            next_date: inc.next_date,
          }),
        })
      }
      onNext()
    } catch (e: any) {
      setError(e.message || '儲存失敗')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">步驟 3：設定收入</h2>
      <p className="text-gray-600 text-sm">輸入你的薪資或其他固定收入。</p>

      {incomes.map((inc, i) => (
        <div key={i} className="flex gap-2 items-end">
          <div className="flex-1">
            <label className="text-xs text-gray-500">名稱</label>
            <input className="w-full border rounded px-3 py-2" placeholder="如：薪水"
              value={inc.name} onChange={(e) => updateRow(i, 'name', e.target.value)} />
          </div>
          <div className="w-28">
            <label className="text-xs text-gray-500">金額</label>
            <input type="number" className="w-full border rounded px-3 py-2" placeholder="50000"
              value={inc.amount} onChange={(e) => updateRow(i, 'amount', e.target.value)} />
          </div>
          <div className="w-28">
            <label className="text-xs text-gray-500">頻率</label>
            <select className="w-full border rounded px-3 py-2"
              value={inc.frequency} onChange={(e) => updateRow(i, 'frequency', e.target.value)}>
              <option value="monthly">每月</option>
              <option value="biweekly">雙週</option>
              <option value="quarterly">每季</option>
              <option value="yearly">每年</option>
              <option value="once">一次性</option>
            </select>
          </div>
          <div className="w-36">
            <label className="text-xs text-gray-500">下次入帳日</label>
            <input type="date" className="w-full border rounded px-3 py-2"
              value={inc.next_date} onChange={(e) => updateRow(i, 'next_date', e.target.value)} />
          </div>
          {incomes.length > 1 && (
            <button onClick={() => removeRow(i)} className="text-red-400 hover:text-red-600 pb-2">✕</button>
          )}
        </div>
      ))}

      <button onClick={addRow} className="text-indigo-600 text-sm hover:underline">+ 新增收入</button>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      <div className="flex justify-between pt-4">
        <button onClick={onPrev} className="text-gray-500 hover:text-gray-700">上一步</button>
        <button onClick={handleSave} disabled={saving} className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50">
          {saving ? '儲存中...' : '下一步'}
        </button>
      </div>
    </div>
  )
}
