import { useEffect } from 'react'
import AvailableAmount from '../components/AvailableAmount'
import BalanceSummary from '../components/BalanceSummary'
import UpcomingDues from '../components/UpcomingDues'
import StaleBalanceWarning from '../components/StaleBalanceWarning'
import BalanceChart from '../components/BalanceChart'
import { useDashboardSummary } from '../hooks/useDashboard'
import { useAdvanceCycles, useLoadSampleData } from '../hooks/useSystem'

export default function Dashboard() {
  const advanceCycles = useAdvanceCycles()
  const loadSample = useLoadSampleData()
  const { data: summary } = useDashboardSummary()

  useEffect(() => {
    advanceCycles.mutate()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="space-y-6 mt-4">
      <AvailableAmount />
      {summary?.stale_accounts && (
        <StaleBalanceWarning accounts={summary.stale_accounts} />
      )}
      {summary?.upcoming_dues && (
        <UpcomingDues dues={summary.upcoming_dues} />
      )}
      <BalanceChart />
      <BalanceSummary />
      <div className="border-t pt-4">
        <button
          onClick={() => loadSample.mutate()}
          disabled={loadSample.isPending}
          className="text-sm text-indigo-600 hover:text-indigo-800 underline"
        >
          {loadSample.isPending ? '載入中...' : '載入範例資料'}
        </button>
      </div>
    </div>
  )
}
