import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { Account } from '../api/types'

export function useIsFirstTimeUser() {
  const { data: accounts, isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: () => apiFetch<Account[]>('/accounts'),
  })
  return {
    isFirstTime: !isLoading && accounts !== undefined && accounts.length === 0,
    isLoading,
  }
}

export function useAdvanceCycles() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiFetch('/system/advance-cycles', { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries(),
  })
}

export function useLoadSampleData() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => apiFetch('/system/load-sample-data', { method: 'POST' }),
    onSuccess: () => qc.invalidateQueries(),
  })
}
