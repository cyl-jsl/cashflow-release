// src/pages/Incomes.tsx
import { useState } from 'react'
import {
  useIncomes,
  useCreateIncome,
  useUpdateIncome,
  useDeleteIncome,
} from '../hooks/useIncomes'
import type { Income } from '../api/types'
import IncomeActualsList from '../components/IncomeActualsList'

const FREQUENCIES: Record<string, string> = {
  monthly: '每月',
  biweekly: '雙週',
  quarterly: '每季',
  yearly: '每年',
  once: '一次性',
}

function IncomeForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<Income>
  onSubmit: (data: Partial<Income>) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [amount, setAmount] = useState(initial?.amount?.toString() ?? '')
  const [frequency, setFrequency] = useState<Income['frequency']>(initial?.frequency ?? 'monthly')
  const [startDate, setStartDate] = useState(initial?.start_date ?? '')
  const [endDate, setEndDate] = useState(initial?.end_date ?? '')
  const [note, setNote] = useState(initial?.note ?? '')

  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-3">
      <input className="w-full border rounded px-3 py-2" placeholder="收入名稱"
        value={name} onChange={(e) => setName(e.target.value)} />
      <input className="w-full border rounded px-3 py-2" type="number" placeholder="金額"
        value={amount} onChange={(e) => setAmount(e.target.value)} />
      <select className="w-full border rounded px-3 py-2"
        value={frequency} onChange={(e) => setFrequency(e.target.value as Income['frequency'])}>
        {Object.entries(FREQUENCIES).map(([v, l]) => (
          <option key={v} value={v}>{l}</option>
        ))}
      </select>
      <input className="w-full border rounded px-3 py-2" type="date" placeholder="起始日期"
        value={startDate} onChange={(e) => setStartDate(e.target.value)} />
      <input className="w-full border rounded px-3 py-2" type="date" placeholder="結束日期（選填）"
        value={endDate} onChange={(e) => setEndDate(e.target.value)} />
      <input className="w-full border rounded px-3 py-2" placeholder="備註（選填）"
        value={note} onChange={(e) => setNote(e.target.value)} />
      <div className="flex gap-2">
        <button className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
          onClick={() => onSubmit({
            name, amount: parseFloat(amount), frequency,
            start_date: startDate, end_date: endDate || undefined, note: note || undefined,
          })}>
          儲存
        </button>
        <button className="px-4 py-2 rounded border" onClick={onCancel}>取消</button>
      </div>
    </div>
  )
}

export default function Incomes() {
  const { data: incomes, isLoading } = useIncomes()
  const createIncome = useCreateIncome()
  const updateIncome = useUpdateIncome()
  const deleteIncome = useDeleteIncome()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  if (isLoading) return <div className="animate-pulse h-48 bg-gray-100 rounded-lg mt-4" />

  return (
    <div className="mt-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold">收入管理</h1>
        <button className="bg-indigo-600 text-white px-4 py-2 rounded text-sm hover:bg-indigo-700"
          onClick={() => { setShowForm(true); setEditingId(null) }}>
          新增收入
        </button>
      </div>

      {showForm && !editingId && (
        <IncomeForm
          onSubmit={(data) => createIncome.mutate(data, { onSuccess: () => setShowForm(false) })}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className="space-y-2">
        {incomes?.map((income) => (
          <div key={income.id} className="bg-white border rounded-lg p-4">
            {editingId === income.id ? (
              <IncomeForm
                initial={income}
                onSubmit={(data) => updateIncome.mutate(
                  { id: income.id, ...data },
                  { onSuccess: () => setEditingId(null) },
                )}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <>
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium">{income.name}</p>
                    <p className="text-sm text-gray-500">
                      {FREQUENCIES[income.frequency]} ·{' '}
                      {new Intl.NumberFormat('zh-TW', { style: 'currency', currency: 'TWD', minimumFractionDigits: 0 }).format(income.amount)}
                      {' · 下次入帳 '}{income.next_date}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button className="text-sm text-indigo-600 hover:underline"
                      onClick={() => setEditingId(income.id)}>編輯</button>
                    <button className="text-sm text-red-600 hover:underline"
                      onClick={() => { if (confirm('確定刪除？')) deleteIncome.mutate(income.id) }}>
                      刪除
                    </button>
                  </div>
                </div>
                <IncomeActualsList income={income} />
              </>
            )}
          </div>
        ))}
        {!incomes?.length && <p className="text-gray-500 text-center py-8">尚未建立收入</p>}
      </div>
    </div>
  )
}
