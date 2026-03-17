import { useState } from 'react'
import { apiFetch } from '../../api/client'

export default function AccountStep({ onNext, onPrev }: { onNext: () => void; onPrev: () => void }) {
  const [accounts, setAccounts] = useState<{ name: string; type: string; balance: string }[]>([
    { name: '', type: 'bank', balance: '' },
  ])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const addRow = () => setAccounts([...accounts, { name: '', type: 'bank', balance: '' }])
  const removeRow = (i: number) => setAccounts(accounts.filter((_, idx) => idx !== i))
  const updateRow = (i: number, field: string, value: string) => {
    const updated = [...accounts]
    updated[i] = { ...updated[i], [field]: value }
    setAccounts(updated)
  }

  const handleSave = async () => {
    const valid = accounts.filter((a) => a.name.trim() && a.balance.trim())
    if (valid.length === 0) {
      setError('請至少建立一個帳戶')
      return
    }
    setSaving(true)
    setError('')
    try {
      for (const a of valid) {
        await apiFetch('/accounts', {
          method: 'POST',
          body: JSON.stringify({
            name: a.name.trim(),
            type: a.type,
            balance: parseFloat(a.balance) || 0,
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
      <h2 className="text-xl font-bold">步驟 2：建立帳戶</h2>
      <p className="text-gray-600 text-sm">輸入你的銀行帳戶和目前餘額。稍後可隨時修改。</p>

      {accounts.map((a, i) => (
        <div key={i} className="flex gap-2 items-end">
          <div className="flex-1">
            <label className="text-xs text-gray-500">名稱</label>
            <input
              className="w-full border rounded px-3 py-2"
              placeholder="如：中信薪轉"
              value={a.name}
              onChange={(e) => updateRow(i, 'name', e.target.value)}
            />
          </div>
          <div className="w-28">
            <label className="text-xs text-gray-500">類型</label>
            <select
              className="w-full border rounded px-3 py-2"
              value={a.type}
              onChange={(e) => updateRow(i, 'type', e.target.value)}
            >
              <option value="bank">銀行</option>
              <option value="cash">現金</option>
              <option value="investment">投資</option>
            </select>
          </div>
          <div className="w-32">
            <label className="text-xs text-gray-500">餘額</label>
            <input
              type="number"
              className="w-full border rounded px-3 py-2"
              placeholder="0"
              value={a.balance}
              onChange={(e) => updateRow(i, 'balance', e.target.value)}
            />
          </div>
          {accounts.length > 1 && (
            <button onClick={() => removeRow(i)} className="text-red-400 hover:text-red-600 pb-2">✕</button>
          )}
        </div>
      ))}

      <button onClick={addRow} className="text-indigo-600 text-sm hover:underline">
        + 新增帳戶
      </button>

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
