import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { Obligation } from '../api/types'

export function useObligations(type?: string) {
  const params = type ? `?type=${type}` : ''
  return useQuery({
    queryKey: ['obligations', type],
    queryFn: () => apiFetch<Obligation[]>(`/obligations${params}`),
  })
}

export function useCreateObligation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<Obligation>) =>
      apiFetch<Obligation>('/obligations', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['obligations'] }),
  })
}

export function useUpdateObligation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<Obligation> & { id: number }) =>
      apiFetch<Obligation>(`/obligations/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['obligations'] }),
  })
}

export function useDeleteObligation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/obligations/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['obligations'] }),
  })
}
