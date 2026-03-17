import { useState } from 'react'
import { useForecastAvailable } from '../hooks/useForecast'
import { formatCurrency } from '../utils/format'

type PeriodMode = 'end_of_month' | 'next_payday' | 'days' | 'custom'

const MODE_OPTIONS: { value: PeriodMode; label: string }[] = [
  { value: 'end_of_month', label: '到月底' },
  { value: 'next_payday', label: '到發薪日' },
  { value: 'days', label: 'N 天後' },
  { value: 'custom', label: '自訂日期' },
]

export default function AvailableAmount() {
  const [mode, setMode] = useState<PeriodMode>('end_of_month')
  const [daysValue, setDaysValue] = useState(30)
  const [customDate, setCustomDate] = useState('')

  const params = (() => {
    if (mode === 'custom') {
      if (customDate) return { until: customDate }
      return { periodType: 'end_of_month' }  // fallback until user picks a date
    }
    if (mode === 'days') return { periodType: 'days', periodValue: daysValue }
    return { periodType: mode }
  })()

  const { data, isLoading, error } = useForecastAvailable(params)

  if (isLoading) return <div className="animate-pulse h-32 bg-gray-100 rounded-lg" />
  if (error) return <div className="text-red-600">載入失敗</div>
  if (!data) return null

  const label = MODE_OPTIONS.find(o => o.value === mode)?.label ?? mode

  return (
    <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 rounded-xl p-6 text-white">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <p className="text-indigo-200 text-sm">可動用金額（{label}）</p>
        <div className="flex gap-1 items-center">
          {MODE_OPTIONS.map(opt => (
            <button
              key={opt.value}
              onClick={() => setMode(opt.value)}
              className={`text-xs px-2 py-1 rounded ${
                mode === opt.value
                  ? 'bg-white/20 text-white'
                  : 'text-indigo-300 hover:bg-white/10'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
      {mode === 'days' && (
        <div className="mt-2 flex items-center gap-2">
          <input
            type="number"
            min="1"
            max="365"
            value={daysValue}
            onChange={(e) => setDaysValue(parseInt(e.target.value) || 30)}
            className="w-20 rounded px-2 py-1 text-sm text-gray-800"
          />
          <span className="text-indigo-300 text-xs">天</span>
        </div>
      )}
      {mode === 'custom' && (
        <div className="mt-2">
          <input
            type="date"
            value={customDate}
            onChange={(e) => setCustomDate(e.target.value)}
            className="rounded px-2 py-1 text-sm text-gray-800"
          />
        </div>
      )}
      <p className="text-4xl font-bold mt-1">{formatCurrency(data.available_amount)}</p>
      <p className="text-indigo-300 text-xs mt-2">
        {data.period.from} ~ {data.period.until}
      </p>
      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-indigo-300">帳戶餘額</p>
          <p className="font-semibold">{formatCurrency(data.total_balance)}</p>
        </div>
        <div>
          <p className="text-indigo-300">期間收入</p>
          <p className="font-semibold text-green-300">+{formatCurrency(data.period_income)}</p>
        </div>
        <div>
          <p className="text-indigo-300">期間支出</p>
          <p className="font-semibold text-red-300">
            -{formatCurrency(data.period_obligations + data.period_credit_card_bills)}
          </p>
        </div>
      </div>
    </div>
  )
}
