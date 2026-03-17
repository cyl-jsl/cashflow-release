import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { CreditCard } from '../api/types'

export function useCreditCards() {
  return useQuery({
    queryKey: ['credit-cards'],
    queryFn: () => apiFetch<CreditCard[]>('/credit-cards'),
  })
}

export function useCreateCreditCard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Partial<CreditCard>) =>
      apiFetch<CreditCard>('/credit-cards', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credit-cards'] }),
  })
}

export function useUpdateCreditCard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<CreditCard> & { id: number }) =>
      apiFetch<CreditCard>(`/credit-cards/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credit-cards'] }),
  })
}

export function useDeleteCreditCard() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/credit-cards/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credit-cards'] }),
  })
}
