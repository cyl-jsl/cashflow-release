import { useState, useEffect } from 'react'
import { useAccounts, useBatchUpdateBalances } from '../hooks/useAccounts'
import { formatCurrency } from '../utils/format'

export default function QuickUpdateBalances({ onClose }: { onClose: () => void }) {
  const { data: accounts } = useAccounts()
  const batchUpdate = useBatchUpdateBalances()
  const [balances, setBalances] = useState<Record<number, string>>({})

  useEffect(() => {
    if (accounts) {
      const initial: Record<number, string> = {}
      for (const a of accounts) {
        initial[a.id] = a.balance.toString()
      }
      setBalances(initial)
    }
  }, [accounts])

  const handleSave = () => {
    if (!accounts) return
    const updates = accounts
      .filter(a => parseFloat(balances[a.id] ?? '0') !== a.balance)
      .map(a => ({ id: a.id, balance: parseFloat(balances[a.id] ?? '0') }))

    if (updates.length === 0) {
      onClose()
      return
    }

    batchUpdate.mutate(updates, { onSuccess: () => onClose() })
  }

  if (!accounts) return null

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">快速更新餘額</h2>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-sm">
          取消
        </button>
      </div>
      <p className="text-sm text-gray-600">一次更新所有帳戶的最新餘額</p>
      <div className="space-y-3">
        {accounts.map((account) => (
          <div key={account.id} className="flex items-center gap-3">
            <label className="w-32 text-sm font-medium truncate">{account.name}</label>
            <span className="text-xs text-gray-400 w-24">
              現有 {formatCurrency(account.balance)}
            </span>
            <input
              type="number"
              className="flex-1 border rounded px-3 py-1.5"
              value={balances[account.id] ?? ''}
              onChange={(e) => setBalances(prev => ({ ...prev, [account.id]: e.target.value }))}
            />
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={batchUpdate.isPending}
          className="bg-amber-600 text-white px-4 py-2 rounded hover:bg-amber-700 disabled:opacity-50"
        >
          {batchUpdate.isPending ? '儲存中...' : '全部儲存'}
        </button>
        <button onClick={onClose} className="px-4 py-2 rounded border">
          取消
        </button>
      </div>
    </div>
  )
}
