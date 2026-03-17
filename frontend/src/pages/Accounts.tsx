// src/pages/Accounts.tsx
import { useState } from 'react'
import {
  useAccounts,
  useCreateAccount,
  useUpdateAccount,
  useDeleteAccount,
} from '../hooks/useAccounts'
import type { Account } from '../api/types'
import QuickUpdateBalances from '../components/QuickUpdateBalances'

const TYPES = [
  { value: 'bank', label: '銀行' },
  { value: 'cash', label: '現金' },
  { value: 'investment', label: '投資' },
] as const

function AccountForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<Account>
  onSubmit: (data: Partial<Account>) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [type, setType] = useState(initial?.type ?? 'bank')
  const [balance, setBalance] = useState(initial?.balance?.toString() ?? '0')
  const [note, setNote] = useState(initial?.note ?? '')

  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-3">
      <input
        className="w-full border rounded px-3 py-2"
        placeholder="帳戶名稱"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <select
        className="w-full border rounded px-3 py-2"
        value={type}
        onChange={(e) => setType(e.target.value as Account['type'])}
      >
        {TYPES.map((t) => (
          <option key={t.value} value={t.value}>{t.label}</option>
        ))}
      </select>
      <input
        className="w-full border rounded px-3 py-2"
        type="number"
        placeholder="餘額"
        value={balance}
        onChange={(e) => setBalance(e.target.value)}
      />
      <input
        className="w-full border rounded px-3 py-2"
        placeholder="備註（選填）"
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
      <div className="flex gap-2">
        <button
          className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
          onClick={() => onSubmit({ name, type, balance: parseFloat(balance), note: note || undefined })}
        >
          儲存
        </button>
        <button className="px-4 py-2 rounded border" onClick={onCancel}>
          取消
        </button>
      </div>
    </div>
  )
}

export default function Accounts() {
  const { data: accounts, isLoading } = useAccounts()
  const createAccount = useCreateAccount()
  const updateAccount = useUpdateAccount()
  const deleteAccount = useDeleteAccount()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [showQuickUpdate, setShowQuickUpdate] = useState(false)

  if (isLoading) return <div className="animate-pulse h-48 bg-gray-100 rounded-lg mt-4" />

  return (
    <div className="mt-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold">帳戶管理</h1>
        <div className="flex gap-2">
          <button
            className="bg-amber-500 text-white px-4 py-2 rounded text-sm hover:bg-amber-600"
            onClick={() => setShowQuickUpdate(true)}
          >
            快速更新餘額
          </button>
          <button
            className="bg-indigo-600 text-white px-4 py-2 rounded text-sm hover:bg-indigo-700"
            onClick={() => { setShowForm(true); setEditingId(null) }}
          >
            新增帳戶
          </button>
        </div>
      </div>

      {showQuickUpdate && (
        <QuickUpdateBalances onClose={() => setShowQuickUpdate(false)} />
      )}

      {showForm && !editingId && (
        <AccountForm
          onSubmit={(data) => {
            createAccount.mutate(data, { onSuccess: () => setShowForm(false) })
          }}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className="space-y-2">
        {accounts?.map((account) => (
          <div key={account.id} className="bg-white border rounded-lg p-4">
            {editingId === account.id ? (
              <AccountForm
                initial={account}
                onSubmit={(data) => {
                  updateAccount.mutate(
                    { id: account.id, ...data },
                    { onSuccess: () => setEditingId(null) },
                  )
                }}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-medium">{account.name}</p>
                  <p className="text-sm text-gray-500">
                    {TYPES.find((t) => t.value === account.type)?.label} ·{' '}
                    {new Intl.NumberFormat('zh-TW', { style: 'currency', currency: 'TWD', minimumFractionDigits: 0 }).format(account.balance)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    className="text-sm text-indigo-600 hover:underline"
                    onClick={() => setEditingId(account.id)}
                  >
                    編輯
                  </button>
                  <button
                    className="text-sm text-red-600 hover:underline"
                    onClick={() => {
                      if (confirm('確定刪除？')) deleteAccount.mutate(account.id)
                    }}
                  >
                    刪除
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
        {!accounts?.length && <p className="text-gray-500 text-center py-8">尚未建立帳戶</p>}
      </div>
    </div>
  )
}
