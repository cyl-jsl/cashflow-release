import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { CanISpendRequest, CanISpendResponse, SavingsGoalRequest, SavingsGoalResponse } from '../api/types'

export function useCanISpend() {
  return useMutation({
    mutationFn: (data: CanISpendRequest) =>
      apiFetch<CanISpendResponse>('/planning/can-i-spend', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useSavingsGoal() {
  return useMutation({
    mutationFn: (data: SavingsGoalRequest) =>
      apiFetch<SavingsGoalResponse>('/planning/savings-goal', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}
