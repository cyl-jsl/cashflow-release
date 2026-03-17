import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { ForecastAvailable, TimelineData } from '../api/types'

export function useForecastAvailable(params?: {
  periodType?: string
  periodValue?: number
  until?: string
}) {
  const searchParams = new URLSearchParams()
  if (params?.until) {
    searchParams.set('until', params.until)
  } else if (params?.periodType) {
    searchParams.set('period_type', params.periodType)
    if (params.periodValue) searchParams.set('period_value', params.periodValue.toString())
  }
  const qs = searchParams.toString()
  const url = qs ? `/forecast/available?${qs}` : '/forecast/available'

  return useQuery({
    queryKey: ['forecast', 'available', params],
    queryFn: () => apiFetch<ForecastAvailable>(url),
  })
}

export function useForecastTimeline(months: number = 6) {
  return useQuery({
    queryKey: ['forecast', 'timeline', months],
    queryFn: () => apiFetch<TimelineData>(`/forecast/timeline?months=${months}`),
  })
}
