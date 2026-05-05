import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { IncomeAdjustment } from '../api/types'

export function useIncomeAdjustments(incomeId: number | null) {
  return useQuery({
    queryKey: ['income-adjustments', incomeId],
    queryFn: () =>
      apiFetch<IncomeAdjustment[]>(`/incomes/${incomeId}/adjustments`),
    enabled: incomeId != null,
  })
}

export function useUpsertIncomeActual(incomeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: {
      effective_date: string
      actual_amount: number
      note?: string | null
    }) =>
      apiFetch<IncomeAdjustment>(`/incomes/${incomeId}/actuals`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['income-adjustments', incomeId] })
      qc.invalidateQueries({ queryKey: ['forecast'] })
      qc.invalidateQueries({ queryKey: ['dashboard-summary'] })
    },
  })
}

export function useDeleteIncomeAdjustment(incomeId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (adjustmentId: number) =>
      apiFetch(`/income-adjustments/${adjustmentId}`, { method: 'DELETE' }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['income-adjustments', incomeId] })
      qc.invalidateQueries({ queryKey: ['forecast'] })
      qc.invalidateQueries({ queryKey: ['dashboard-summary'] })
    },
  })
}
