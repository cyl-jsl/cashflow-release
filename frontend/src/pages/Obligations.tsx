// src/pages/Obligations.tsx
import { useState } from 'react'
import {
  useObligations,
  useCreateObligation,
  useUpdateObligation,
  useDeleteObligation,
} from '../hooks/useObligations'
import type { Obligation } from '../api/types'

const FREQUENCIES: Record<string, string> = {
  monthly: '每月', biweekly: '雙週', quarterly: '每季', yearly: '每年', once: '一次性',
}
const TYPES: Record<string, string> = {
  fixed: '固定支出', budget: '預估生活費',
}
const TYPE_FILTERS = [
  { value: undefined, label: '全部' },
  { value: 'fixed', label: '固定支出' },
  { value: 'budget', label: '預估生活費' },
] as const

function ObligationForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<Obligation>
  onSubmit: (data: Partial<Obligation>) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [type, setType] = useState<Obligation['type']>(initial?.type ?? 'fixed')
  const [amount, setAmount] = useState(initial?.amount?.toString() ?? '')
  const [frequency, setFrequency] = useState<Obligation['frequency']>(initial?.frequency ?? 'monthly')
  const [startDate, setStartDate] = useState(initial?.start_date ?? '')
  const [endDate, setEndDate] = useState(initial?.end_date ?? '')
  const [note, setNote] = useState(initial?.note ?? '')

  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-3">
      <input className="w-full border rounded px-3 py-2" placeholder="義務名稱"
        value={name} onChange={(e) => setName(e.target.value)} />
      <select className="w-full border rounded px-3 py-2"
        value={type} onChange={(e) => setType(e.target.value as Obligation['type'])}>
        {Object.entries(TYPES).map(([v, l]) => (
          <option key={v} value={v}>{l}</option>
        ))}
      </select>
      <input className="w-full border rounded px-3 py-2" type="number" placeholder="金額"
        value={amount} onChange={(e) => setAmount(e.target.value)} />
      <select className="w-full border rounded px-3 py-2"
        value={frequency} onChange={(e) => setFrequency(e.target.value as Obligation['frequency'])}>
        {Object.entries(FREQUENCIES).map(([v, l]) => (
          <option key={v} value={v}>{l}</option>
        ))}
      </select>
      <input className="w-full border rounded px-3 py-2" type="date"
        value={startDate} onChange={(e) => setStartDate(e.target.value)} />
      <input className="w-full border rounded px-3 py-2" type="date" placeholder="結束日期（選填）"
        value={endDate} onChange={(e) => setEndDate(e.target.value)} />
      <input className="w-full border rounded px-3 py-2" placeholder="備註（選填）"
        value={note} onChange={(e) => setNote(e.target.value)} />
      <div className="flex gap-2">
        <button className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
          onClick={() => onSubmit({
            name, type, amount: parseFloat(amount),
            frequency,
            start_date: startDate, end_date: endDate || undefined, note: note || undefined,
          })}>
          儲存
        </button>
        <button className="px-4 py-2 rounded border" onClick={onCancel}>取消</button>
      </div>
    </div>
  )
}

export default function Obligations() {
  const [filterType, setFilterType] = useState<string | undefined>(undefined)
  const { data: obligations, isLoading } = useObligations(filterType)
  const createObligation = useCreateObligation()
  const updateObligation = useUpdateObligation()
  const deleteObligation = useDeleteObligation()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)

  if (isLoading) return <div className="animate-pulse h-48 bg-gray-100 rounded-lg mt-4" />

  return (
    <div className="mt-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold">義務管理</h1>
        <button className="bg-indigo-600 text-white px-4 py-2 rounded text-sm hover:bg-indigo-700"
          onClick={() => { setShowForm(true); setEditingId(null) }}>
          新增義務
        </button>
      </div>

      {/* Type filter */}
      <div className="flex gap-2">
        {TYPE_FILTERS.map((f) => (
          <button
            key={f.label}
            className={`px-3 py-1 rounded-full text-sm ${
              filterType === f.value
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
            onClick={() => setFilterType(f.value)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {showForm && !editingId && (
        <ObligationForm
          onSubmit={(data) => createObligation.mutate(data, { onSuccess: () => setShowForm(false) })}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className="space-y-2">
        {obligations?.map((ob) => (
          <div key={ob.id} className="bg-white border rounded-lg p-4">
            {editingId === ob.id ? (
              <ObligationForm
                initial={ob}
                onSubmit={(data) => updateObligation.mutate(
                  { id: ob.id, ...data },
                  { onSuccess: () => setEditingId(null) },
                )}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <div className="flex justify-between items-center">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{ob.name}</p>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                      {TYPES[ob.type] ?? ob.type}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    {FREQUENCIES[ob.frequency]} ·{' '}
                    {new Intl.NumberFormat('zh-TW', { style: 'currency', currency: 'TWD', minimumFractionDigits: 0 }).format(ob.amount)}
                    {' · 下次到期 '}{ob.next_due_date}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button className="text-sm text-indigo-600 hover:underline"
                    onClick={() => setEditingId(ob.id)}>編輯</button>
                  <button className="text-sm text-red-600 hover:underline"
                    onClick={() => { if (confirm('確定刪除？')) deleteObligation.mutate(ob.id) }}>
                    刪除
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
        {!obligations?.length && <p className="text-gray-500 text-center py-8">尚未建立義務</p>}
      </div>
    </div>
  )
}
