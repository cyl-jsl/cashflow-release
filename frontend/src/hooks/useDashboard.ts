import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { DashboardSummary } from '../api/types'

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => apiFetch<DashboardSummary>('/dashboard/summary'),
  })
}
