import type { UpcomingDue } from '../api/types'

const fmt = (n: number) =>
  new Intl.NumberFormat('zh-TW', {
    style: 'currency', currency: 'TWD', minimumFractionDigits: 0,
  }).format(n)

export default function UpcomingDues({ dues }: { dues: UpcomingDue[] }) {
  if (!dues.length) {
    return (
      <div className="bg-white rounded-xl border p-4">
        <h2 className="text-sm font-medium text-gray-500 mb-2">近期到期</h2>
        <p className="text-gray-400 text-sm">7 天內無到期項目</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl border p-4">
      <h2 className="text-sm font-medium text-gray-500 mb-3">近期到期（7 天內）</h2>
      <div className="space-y-2">
        {dues.map((due, i) => (
          <div key={i} className="flex justify-between items-center text-sm">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                due.type === 'credit_card_bill'
                  ? due.is_paid ? 'bg-green-400' : 'bg-orange-400'
                  : 'bg-blue-400'
              }`} />
              <span className="text-gray-700">{due.name}</span>
              {due.type === 'credit_card_bill' && due.is_paid && (
                <span className="text-xs text-green-600 bg-green-50 px-1.5 py-0.5 rounded">已繳</span>
              )}
            </div>
            <div className="text-right">
              <span className="font-medium">{fmt(due.amount)}</span>
              <span className="text-gray-400 ml-2 text-xs">{due.due_date}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
