import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  useCreditCards,
  useCreateCreditCard,
  useUpdateCreditCard,
  useDeleteCreditCard,
} from '../hooks/useCreditCards'
import {
  useCreditCardBills,
  useCreateCreditCardBill,
  useUpdateCreditCardBill,
  useDeleteCreditCardBill,
} from '../hooks/useCreditCardBills'
import { apiFetch } from '../api/client'
import type { CreditCard, CreditCardBill } from '../api/types'

const fmt = (n: number) =>
  new Intl.NumberFormat('zh-TW', {
    style: 'currency', currency: 'TWD', minimumFractionDigits: 0,
  }).format(n)

function CardForm({
  initial,
  onSubmit,
  onCancel,
}: {
  initial?: Partial<CreditCard>
  onSubmit: (data: Partial<CreditCard>) => void
  onCancel: () => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [billingDay, setBillingDay] = useState(initial?.billing_day?.toString() ?? '')
  const [dueDay, setDueDay] = useState(initial?.due_day?.toString() ?? '')
  const [creditLimit, setCreditLimit] = useState(initial?.credit_limit?.toString() ?? '')
  const [note, setNote] = useState(initial?.note ?? '')
  const [revolvingRate, setRevolvingRate] = useState(initial?.revolving_interest_rate?.toString() ?? '')

  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-3">
      <input className="w-full border rounded px-3 py-2" placeholder="卡片名稱"
        value={name} onChange={(e) => setName(e.target.value)} />
      <div className="grid grid-cols-2 gap-3">
        <input className="border rounded px-3 py-2" type="number" placeholder="結帳日 (1-28)"
          value={billingDay} onChange={(e) => setBillingDay(e.target.value)} />
        <input className="border rounded px-3 py-2" type="number" placeholder="繳款日 (1-28)"
          value={dueDay} onChange={(e) => setDueDay(e.target.value)} />
      </div>
      <input className="w-full border rounded px-3 py-2" type="number" placeholder="信用額度（選填）"
        value={creditLimit} onChange={(e) => setCreditLimit(e.target.value)} />
      <input className="w-full border rounded px-3 py-2" type="number" step="0.01"
        placeholder="循環利率（年，如 0.15 = 15%，選填）"
        value={revolvingRate} onChange={(e) => setRevolvingRate(e.target.value)} />
      <input className="w-full border rounded px-3 py-2" placeholder="備註（選填）"
        value={note} onChange={(e) => setNote(e.target.value)} />
      <div className="flex gap-2">
        <button className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
          onClick={() => onSubmit({
            name,
            billing_day: parseInt(billingDay),
            due_day: parseInt(dueDay),
            credit_limit: creditLimit ? parseFloat(creditLimit) : undefined,
            revolving_interest_rate: revolvingRate ? parseFloat(revolvingRate) : null,
            note: note || undefined,
          } as Partial<CreditCard>)}>
          儲存
        </button>
        <button className="px-4 py-2 rounded border" onClick={onCancel}>取消</button>
      </div>
    </div>
  )
}

function BillForm({
  cardId,
  onSubmit,
  onCancel,
}: {
  cardId: number
  onSubmit: (data: Record<string, unknown>) => void
  onCancel: () => void
}) {
  const [year, setYear] = useState(new Date().getFullYear().toString())
  const [month, setMonth] = useState((new Date().getMonth() + 1).toString())
  const [dueDate, setDueDate] = useState('')
  const [generalSpending, setGeneralSpending] = useState('')

  return (
    <div className="bg-blue-50 rounded-lg p-4 space-y-3 mt-2">
      <div className="grid grid-cols-2 gap-3">
        <input className="border rounded px-3 py-2" type="number" placeholder="年份"
          value={year} onChange={(e) => setYear(e.target.value)} />
        <input className="border rounded px-3 py-2" type="number" placeholder="月份"
          value={month} onChange={(e) => setMonth(e.target.value)} />
      </div>
      <input className="w-full border rounded px-3 py-2" type="date" placeholder="繳款截止日"
        value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
      <input className="w-full border rounded px-3 py-2" type="number" placeholder="一般消費金額"
        value={generalSpending} onChange={(e) => setGeneralSpending(e.target.value)} />
      <div className="flex gap-2">
        <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          onClick={() => onSubmit({
            credit_card_id: cardId,
            billing_year: parseInt(year),
            billing_month: parseInt(month),
            due_date: dueDate,
            general_spending: parseFloat(generalSpending) || 0,
          })}>
          新增帳單
        </button>
        <button className="px-4 py-2 rounded border" onClick={onCancel}>取消</button>
      </div>
    </div>
  )
}

function BillToInstallmentForm({
  bill,
  cardId,
  onSuccess,
  onCancel,
}: {
  bill: CreditCardBill
  cardId: number
  onSuccess: () => void
  onCancel: () => void
}) {
  const [periods, setPeriods] = useState('6')
  const [monthlyAmount, setMonthlyAmount] = useState(
    Math.ceil(bill.total_amount / 6).toString()
  )
  const [fee, setFee] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const qc = useQueryClient()

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      await apiFetch('/obligations', {
        method: 'POST',
        body: JSON.stringify({
          name: `${bill.billing_year}/${bill.billing_month}月帳單分期`,
          type: 'installment',
          amount: parseFloat(monthlyAmount),
          frequency: 'monthly',
          start_date: bill.due_date,
          installment: {
            credit_card_id: cardId,
            installment_type: 'bill',
            source_bill_id: bill.id,
            total_amount: bill.total_amount,
            total_periods: parseInt(periods),
            fee: fee ? parseFloat(fee) : undefined,
          },
        }),
      })
      qc.invalidateQueries({ queryKey: ['credit-card-bills'] })
      qc.invalidateQueries({ queryKey: ['obligations'] })
      onSuccess()
    } catch {
      alert('轉分期失敗')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-indigo-50 rounded-lg p-4 mt-2 space-y-3">
      <p className="text-sm font-medium">將 {fmt(bill.total_amount)} 轉為分期</p>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs text-gray-500">期數</label>
          <input type="number" min="2" max="60" className="w-full border rounded px-2 py-1"
            value={periods} onChange={(e) => {
              setPeriods(e.target.value)
              const p = parseInt(e.target.value) || 6
              setMonthlyAmount(Math.ceil(bill.total_amount / p).toString())
            }} />
        </div>
        <div>
          <label className="text-xs text-gray-500">每月應繳（元）</label>
          <input type="number" className="w-full border rounded px-2 py-1"
            value={monthlyAmount} onChange={(e) => setMonthlyAmount(e.target.value)} />
        </div>
        <div>
          <label className="text-xs text-gray-500">手續費（選填）</label>
          <input type="number" className="w-full border rounded px-2 py-1"
            value={fee} onChange={(e) => setFee(e.target.value)} />
        </div>
      </div>
      <div className="flex gap-2">
        <button className="bg-indigo-600 text-white px-4 py-2 rounded text-sm hover:bg-indigo-700"
          disabled={submitting} onClick={handleSubmit}>
          {submitting ? '處理中...' : '確認轉分期'}
        </button>
        <button className="px-4 py-2 rounded border text-sm" onClick={onCancel}>取消</button>
      </div>
    </div>
  )
}

function CardBills({ cardId }: { cardId: number }) {
  const { data: bills } = useCreditCardBills(cardId)
  const updateBill = useUpdateCreditCardBill()
  const deleteBill = useDeleteCreditCardBill()
  const createBill = useCreateCreditCardBill()
  const [showBillForm, setShowBillForm] = useState(false)
  const [convertingBillId, setConvertingBillId] = useState<number | null>(null)
  const [partialPayment, setPartialPayment] = useState<Record<number, string>>({})

  return (
    <div className="mt-3 pl-4 border-l-2 border-indigo-200">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium text-gray-600">帳單</h3>
        <button className="text-xs text-blue-600 hover:underline"
          onClick={() => setShowBillForm(true)}>
          新增帳單
        </button>
      </div>
      {showBillForm && (
        <BillForm
          cardId={cardId}
          onSubmit={(data) => createBill.mutate(data, { onSuccess: () => setShowBillForm(false) })}
          onCancel={() => setShowBillForm(false)}
        />
      )}
      {bills?.length ? (
        <div className="space-y-2">
          {bills.map((bill) => (
            <div key={bill.id} className="bg-white border rounded p-3 text-sm">
              <div className="flex justify-between items-center">
                <div>
                  <span className="font-medium">{bill.billing_year}/{bill.billing_month}月</span>
                  <span className="text-gray-500 ml-2">繳款日 {bill.due_date}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={bill.is_paid ? 'text-green-600' : 'text-red-600'}>
                    {bill.is_paid ? '已繳' : '未繳'}
                  </span>
                  {!bill.is_paid && (
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        placeholder="繳款金額（空=全額）"
                        className="border rounded px-2 py-1 text-xs w-36"
                        onChange={(e) => setPartialPayment((prev) => ({ ...prev, [bill.id]: e.target.value }))}
                        value={partialPayment[bill.id] || ''}
                      />
                      <button className="text-xs text-green-600 hover:underline"
                        onClick={() => {
                          const paidAmt = partialPayment[bill.id] ? parseFloat(partialPayment[bill.id]) : undefined
                          updateBill.mutate({
                            id: bill.id,
                            is_paid: true,
                            ...(paidAmt !== undefined ? { paid_amount: paidAmt } : {}),
                          })
                        }}>
                        標記已繳
                      </button>
                      <button className="text-xs text-indigo-600 hover:underline"
                        onClick={() => setConvertingBillId(bill.id)}>
                        轉分期
                      </button>
                    </div>
                  )}
                  <button className="text-xs text-red-600 hover:underline"
                    onClick={() => { if (confirm('確定刪除此帳單？')) deleteBill.mutate(bill.id) }}>
                    刪除
                  </button>
                </div>
              </div>
              <div className="mt-1 text-gray-500 grid grid-cols-3 gap-2">
                <span>分期：{fmt(bill.installment_amount)}</span>
                <span>一般消費：{fmt(bill.general_spending)}</span>
                <span className="font-medium text-gray-700">
                  合計：{fmt(bill.total_amount)}
                  {bill.carried_forward > 0 && (
                    <span className="text-orange-600 text-xs ml-1">
                      (含結轉 {fmt(bill.carried_forward)})
                    </span>
                  )}
                </span>
              </div>
              {convertingBillId === bill.id && (
                <BillToInstallmentForm
                  bill={bill}
                  cardId={cardId}
                  onSuccess={() => setConvertingBillId(null)}
                  onCancel={() => setConvertingBillId(null)}
                />
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-gray-400">尚無帳單</p>
      )}
    </div>
  )
}

export default function CreditCards() {
  const { data: cards, isLoading } = useCreditCards()
  const createCard = useCreateCreditCard()
  const updateCard = useUpdateCreditCard()
  const deleteCard = useDeleteCreditCard()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [expandedId, setExpandedId] = useState<number | null>(null)

  if (isLoading) return <div className="animate-pulse h-48 bg-gray-100 rounded-lg mt-4" />

  return (
    <div className="mt-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-xl font-bold">信用卡管理</h1>
        <button className="bg-indigo-600 text-white px-4 py-2 rounded text-sm hover:bg-indigo-700"
          onClick={() => { setShowForm(true); setEditingId(null) }}>
          新增信用卡
        </button>
      </div>

      {showForm && !editingId && (
        <CardForm
          onSubmit={(data) => createCard.mutate(data, { onSuccess: () => setShowForm(false) })}
          onCancel={() => setShowForm(false)}
        />
      )}

      <div className="space-y-3">
        {cards?.map((card) => (
          <div key={card.id} className="bg-white border rounded-lg p-4">
            {editingId === card.id ? (
              <CardForm
                initial={card}
                onSubmit={(data) => updateCard.mutate(
                  { id: card.id, ...data },
                  { onSuccess: () => setEditingId(null) },
                )}
                onCancel={() => setEditingId(null)}
              />
            ) : (
              <>
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium">{card.name}</p>
                    <p className="text-sm text-gray-500">
                      結帳日 {card.billing_day} 號 · 繳款日 {card.due_day} 號
                      {card.credit_limit != null && ` · 額度 ${fmt(card.credit_limit)}`}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button className="text-sm text-indigo-600 hover:underline"
                      onClick={() => setExpandedId(expandedId === card.id ? null : card.id)}>
                      {expandedId === card.id ? '收合' : '帳單'}
                    </button>
                    <button className="text-sm text-indigo-600 hover:underline"
                      onClick={() => setEditingId(card.id)}>編輯</button>
                    <button className="text-sm text-red-600 hover:underline"
                      onClick={() => { if (confirm('確定刪除？將同時刪除關聯帳單與分期')) deleteCard.mutate(card.id) }}>
                      刪除
                    </button>
                  </div>
                </div>
                {expandedId === card.id && <CardBills cardId={card.id} />}
              </>
            )}
          </div>
        ))}
        {!cards?.length && <p className="text-gray-500 text-center py-8">尚未建立信用卡</p>}
      </div>
    </div>
  )
}
