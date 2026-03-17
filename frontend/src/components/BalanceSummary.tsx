import { useAccounts } from '../hooks/useAccounts'

export default function BalanceSummary() {
  const { data: accounts, isLoading } = useAccounts()

  if (isLoading) return <div className="animate-pulse h-24 bg-gray-100 rounded-lg" />
  if (!accounts?.length) return <p className="text-gray-500">尚未建立帳戶</p>

  const total = accounts.reduce((sum, a) => sum + a.balance, 0)

  return (
    <div className="bg-white rounded-xl border p-4">
      <h2 className="text-sm font-medium text-gray-500 mb-3">帳戶總覽</h2>
      <p className="text-2xl font-bold text-gray-900 mb-3">
        {new Intl.NumberFormat('zh-TW', { style: 'currency', currency: 'TWD', minimumFractionDigits: 0 }).format(total)}
      </p>
      <div className="space-y-2">
        {accounts.map((a) => (
          <div key={a.id} className="flex justify-between text-sm">
            <span className="text-gray-600">{a.name}</span>
            <span className="font-medium">
              {new Intl.NumberFormat('zh-TW').format(a.balance)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
