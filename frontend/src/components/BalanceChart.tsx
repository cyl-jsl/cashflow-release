import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { useForecastTimeline } from '../hooks/useForecast'
import { formatCurrency } from '../utils/format'

function formatMonth(dateStr: string): string {
  const [, month] = dateStr.split('-')
  return `${parseInt(month, 10)}月`
}

export default function BalanceChart() {
  const { data, isLoading, error } = useForecastTimeline(6)

  if (isLoading) return <div className="animate-pulse h-64 bg-gray-100 rounded-lg" />
  if (error) return <div className="text-red-600">走勢圖載入失敗</div>
  if (!data?.timeline?.length) return null

  return (
    <div className="bg-white border rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">未來餘額走勢</h2>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data.timeline}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tickFormatter={formatMonth} />
          <YAxis tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}K`} />
          <Tooltip
            formatter={(value) => [formatCurrency(Number(value)), '餘額']}
            labelFormatter={(label) => String(label)}
          />
          <Line
            type="monotone"
            dataKey="balance"
            stroke="#4f46e5"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className="text-xs text-gray-400 mt-2">* 未來月份不含一般消費預估</p>
    </div>
  )
}
