import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from 'recharts'
import { useSimulate } from '../hooks/useSimulation'
import { formatCurrency } from '../utils/format'

export default function Simulate() {
  const [incomeChange, setIncomeChange] = useState('')
  const [expenseChange, setExpenseChange] = useState('')
  const [months, setMonths] = useState('6')
  const simulate = useSimulate()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    simulate.mutate({
      monthly_income_change: parseFloat(incomeChange) || 0,
      monthly_expense_change: parseFloat(expenseChange) || 0,
      months: parseInt(months) || 6,
    })
  }

  const chartData = simulate.data
    ? simulate.data.baseline.map((b, i) => ({
        date: b.date,
        baseline: b.balance,
        simulated: simulate.data!.simulated[i].balance,
      }))
    : []

  return (
    <div className="mt-4 space-y-6">
      <h1 className="text-xl font-bold">情境模擬</h1>
      <p className="text-sm text-gray-500">調整每月收入或支出，看看對未來餘額的影響</p>

      <form onSubmit={handleSubmit} className="bg-white border rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              月收入增減（元）
            </label>
            <input type="number" className="w-full border rounded px-3 py-2"
              placeholder="例如 10000（加薪）或 -5000（減薪）"
              value={incomeChange} onChange={(e) => setIncomeChange(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              月支出增減（元）
            </label>
            <input type="number" className="w-full border rounded px-3 py-2"
              placeholder="例如 15000（新增車貸）或 -1000（取消訂閱）"
              value={expenseChange} onChange={(e) => setExpenseChange(e.target.value)} />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">模擬月數</label>
          <input type="number" min="1" max="24" className="w-32 border rounded px-3 py-2"
            value={months} onChange={(e) => setMonths(e.target.value)} />
        </div>
        <button type="submit" disabled={simulate.isPending}
          className="bg-indigo-600 text-white px-6 py-2 rounded hover:bg-indigo-700 disabled:opacity-50">
          {simulate.isPending ? '模擬中...' : '開始模擬'}
        </button>
      </form>

      {simulate.data && (
        <div className="bg-white border rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-4">餘額走勢對照</h2>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} />
              <YAxis tickFormatter={(v: number) => `${v.toLocaleString()}`} tick={{ fontSize: 12 }} />
              <Tooltip formatter={(v: number) => formatCurrency(v)} />
              <Legend />
              <Line type="monotone" dataKey="baseline" name="目前走勢" stroke="#6366f1" strokeWidth={2} />
              <Line type="monotone" dataKey="simulated" name="模擬走勢" stroke="#f97316" strokeWidth={2} strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>

          <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <div className="bg-indigo-50 rounded-lg p-3">
              <p className="text-gray-500">目前走勢（{months} 個月後）</p>
              <p className="font-semibold text-lg text-indigo-700">
                {formatCurrency(simulate.data.baseline[simulate.data.baseline.length - 1].balance)}
              </p>
            </div>
            <div className="bg-orange-50 rounded-lg p-3">
              <p className="text-gray-500">模擬走勢（{months} 個月後）</p>
              <p className="font-semibold text-lg text-orange-700">
                {formatCurrency(simulate.data.simulated[simulate.data.simulated.length - 1].balance)}
              </p>
            </div>
          </div>
        </div>
      )}

      {simulate.error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
          模擬失敗：{simulate.error.message}
        </div>
      )}
    </div>
  )
}
