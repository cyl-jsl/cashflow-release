import { useState } from 'react'
import { useCanISpend, useSavingsGoal } from '../hooks/usePlanning'
import { formatCurrency } from '../utils/format'
import type { SavingsGoalRequest } from '../api/types'

export default function Planning() {
  const [amount, setAmount] = useState('')
  const canISpend = useCanISpend()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const val = parseFloat(amount)
    if (val > 0) {
      canISpend.mutate({ amount: val })
    }
  }

  // Savings goal state
  const savingsGoal = useSavingsGoal()
  const [targetAmount, setTargetAmount] = useState('')
  const [mode, setMode] = useState<'target_date' | 'monthly_saving'>('target_date')
  const [targetDate, setTargetDate] = useState('')
  const [monthlySaving, setMonthlySaving] = useState('')

  const handleSavingsSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const payload: SavingsGoalRequest = {
      target_amount: parseFloat(targetAmount),
    }
    if (mode === 'target_date') {
      payload.target_date = targetDate
    } else {
      payload.monthly_saving = parseFloat(monthlySaving)
    }
    savingsGoal.mutate(payload)
  }

  return (
    <div className="mt-4 space-y-6">
      <h1 className="text-xl font-bold">試算：我能花這筆錢嗎？</h1>

      <form onSubmit={handleSubmit} className="bg-white border rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            想花多少錢？（元）
          </label>
          <input
            type="number"
            min="1"
            step="1"
            className="w-full border rounded px-3 py-2 text-lg"
            placeholder="例如 5000"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={canISpend.isPending || !amount || parseFloat(amount) <= 0}
          className="bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700 disabled:opacity-50"
        >
          {canISpend.isPending ? '計算中...' : '試算'}
        </button>
      </form>

      {canISpend.data && (
        <div className={`border rounded-xl p-6 ${
          canISpend.data.is_feasible
            ? 'bg-green-50 border-green-200'
            : 'bg-red-50 border-red-200'
        }`}>
          <p className={`text-2xl font-bold ${
            canISpend.data.is_feasible ? 'text-green-700' : 'text-red-700'
          }`}>
            {canISpend.data.is_feasible ? '可以花！' : '建議別花'}
          </p>
          <p className="text-gray-600 mt-2">{canISpend.data.summary}</p>
          <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">花費前可動用</p>
              <p className="font-semibold text-lg">{formatCurrency(canISpend.data.available_before)}</p>
            </div>
            <div>
              <p className="text-gray-500">花費後可動用</p>
              <p className={`font-semibold text-lg ${
                canISpend.data.available_after < 0 ? 'text-red-600' : ''
              }`}>
                {formatCurrency(canISpend.data.available_after)}
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-3">
            計算期間：{canISpend.data.period.from} ~ {canISpend.data.period.until}
          </p>
        </div>
      )}

      {canISpend.error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
          試算失敗：{canISpend.error.message}
        </div>
      )}

      <h2 className="text-xl font-bold mt-8">存錢目標試算</h2>
      <form onSubmit={handleSavingsSubmit} className="bg-white border rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">目標金額（元）</label>
          <input type="number" min="1" className="w-full border rounded px-3 py-2 text-lg"
            placeholder="例如 100000" value={targetAmount}
            onChange={(e) => setTargetAmount(e.target.value)} />
        </div>

        <div className="flex gap-4">
          <label className="flex items-center gap-1">
            <input type="radio" checked={mode === 'target_date'}
              onChange={() => setMode('target_date')} />
            <span className="text-sm">指定目標日期</span>
          </label>
          <label className="flex items-center gap-1">
            <input type="radio" checked={mode === 'monthly_saving'}
              onChange={() => setMode('monthly_saving')} />
            <span className="text-sm">指定每月存入金額</span>
          </label>
        </div>

        {mode === 'target_date' ? (
          <input type="date" className="w-full border rounded px-3 py-2"
            value={targetDate} onChange={(e) => setTargetDate(e.target.value)} />
        ) : (
          <input type="number" min="1" className="w-full border rounded px-3 py-2"
            placeholder="每月存入金額（元）" value={monthlySaving}
            onChange={(e) => setMonthlySaving(e.target.value)} />
        )}

        <button type="submit" disabled={savingsGoal.isPending || !targetAmount}
          className="bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700 disabled:opacity-50">
          {savingsGoal.isPending ? '計算中...' : '試算'}
        </button>
      </form>

      {savingsGoal.data && (
        <div className={`border rounded-xl p-6 ${
          savingsGoal.data.is_feasible ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
        }`}>
          <p className={`text-2xl font-bold ${
            savingsGoal.data.is_feasible ? 'text-green-700' : 'text-red-700'
          }`}>
            {savingsGoal.data.is_feasible ? '可以達成！' : '難度較高'}
          </p>
          <p className="text-gray-600 mt-2">{savingsGoal.data.summary}</p>
          <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">每月可存餘裕</p>
              <p className="font-semibold text-lg">{formatCurrency(savingsGoal.data.monthly_surplus)}</p>
              <p className="text-xs text-gray-400 mt-1">不含未來信用卡一般消費預估</p>
            </div>
            {savingsGoal.data.monthly_needed != null && (
              <div>
                <p className="text-gray-500">每月需存</p>
                <p className="font-semibold text-lg">{formatCurrency(savingsGoal.data.monthly_needed)}</p>
              </div>
            )}
            {savingsGoal.data.months_needed != null && (
              <div>
                <p className="text-gray-500">需要月數</p>
                <p className="font-semibold text-lg">{savingsGoal.data.months_needed} 個月</p>
              </div>
            )}
            {savingsGoal.data.projected_date && (
              <div>
                <p className="text-gray-500">預計達成日</p>
                <p className="font-semibold text-lg">{savingsGoal.data.projected_date}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
