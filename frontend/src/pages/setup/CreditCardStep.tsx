import { useState } from 'react'
import { apiFetch } from '../../api/client'

export default function CreditCardStep({ onFinish, onPrev }: { onFinish: () => void; onPrev: () => void }) {
  const [cards, setCards] = useState<{ name: string; billing_day: string; due_day: string }[]>([
    { name: '', billing_day: '', due_day: '' },
  ])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const addRow = () => setCards([...cards, { name: '', billing_day: '', due_day: '' }])
  const removeRow = (i: number) => setCards(cards.filter((_, idx) => idx !== i))
  const updateRow = (i: number, field: string, value: string) => {
    const updated = [...cards]
    updated[i] = { ...updated[i], [field]: value }
    setCards(updated)
  }

  const handleFinish = async () => {
    const valid = cards.filter((c) => c.name.trim() && c.billing_day && c.due_day)
    // 前端驗證 billing_day / due_day 範圍（API 限制 1~28）
    for (const c of valid) {
      const bd = parseInt(c.billing_day)
      const dd = parseInt(c.due_day)
      if (bd < 1 || bd > 28 || dd < 1 || dd > 28) {
        setError('結帳日和繳款日必須在 1~28 之間')
        return
      }
    }
    if (valid.length > 0) {
      setSaving(true)
      setError('')
      try {
        for (const c of valid) {
          await apiFetch('/credit-cards', {
            method: 'POST',
            body: JSON.stringify({
              name: c.name.trim(),
              billing_day: parseInt(c.billing_day),
              due_day: parseInt(c.due_day),
            }),
          })
        }
      } catch (e: any) {
        setError(e.message || '儲存失敗')
        setSaving(false)
        return
      }
      setSaving(false)
    }
    onFinish()
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">步驟 6：信用卡（選填）</h2>
      <p className="text-gray-600 text-sm">有信用卡的話填上結帳日和繳款日，沒有就直接完成。</p>

      {cards.map((c, i) => (
        <div key={i} className="flex gap-2 items-end">
          <div className="flex-1">
            <label className="text-xs text-gray-500">卡片名稱</label>
            <input className="w-full border rounded px-3 py-2" placeholder="如：中信 LINE Pay"
              value={c.name} onChange={(e) => updateRow(i, 'name', e.target.value)} />
          </div>
          <div className="w-28">
            <label className="text-xs text-gray-500">結帳日</label>
            <input type="number" min="1" max="28" className="w-full border rounded px-3 py-2"
              placeholder="15" value={c.billing_day} onChange={(e) => updateRow(i, 'billing_day', e.target.value)} />
          </div>
          <div className="w-28">
            <label className="text-xs text-gray-500">繳款日</label>
            <input type="number" min="1" max="28" className="w-full border rounded px-3 py-2"
              placeholder="3" value={c.due_day} onChange={(e) => updateRow(i, 'due_day', e.target.value)} />
          </div>
          {cards.length > 1 && (
            <button onClick={() => removeRow(i)} className="text-red-400 hover:text-red-600 pb-2">✕</button>
          )}
        </div>
      ))}

      <button onClick={addRow} className="text-indigo-600 text-sm hover:underline">+ 新增信用卡</button>
      {error && <p className="text-red-600 text-sm">{error}</p>}

      <div className="flex justify-between pt-4">
        <button onClick={onPrev} className="text-gray-500 hover:text-gray-700">上一步</button>
        <button onClick={handleFinish} disabled={saving} className="bg-green-600 text-white px-8 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50">
          {saving ? '儲存中...' : '完成設定'}
        </button>
      </div>
    </div>
  )
}
