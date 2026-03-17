import { useNavigate } from 'react-router-dom'
import type { StaleAccount } from '../api/types'

export default function StaleBalanceWarning({ accounts }: { accounts: StaleAccount[] }) {
  const navigate = useNavigate()

  if (!accounts.length) return null

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
      <h2 className="text-sm font-medium text-amber-800 mb-2">餘額更新提醒</h2>
      <p className="text-xs text-amber-600 mb-3">以下帳戶餘額已超過 7 天未更新，建議更新以確保計算準確</p>
      <div className="space-y-1">
        {accounts.map((a) => (
          <div key={a.id} className="flex justify-between items-center text-sm">
            <span className="text-amber-800">{a.name}</span>
            <span className="text-amber-600 text-xs">{a.days_since_update} 天前更新</span>
          </div>
        ))}
      </div>
      <button
        className="mt-3 text-sm text-amber-700 hover:text-amber-900 underline"
        onClick={() => navigate('/accounts')}
      >
        前往更新餘額
      </button>
    </div>
  )
}
