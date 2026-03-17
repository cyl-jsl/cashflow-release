import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { CreditCardBill } from '../api/types'

export function useCreditCardBills(creditCardId?: number) {
  const params = creditCardId ? `?credit_card_id=${creditCardId}` : ''
  return useQuery({
    queryKey: ['credit-card-bills', creditCardId],
    queryFn: () => apiFetch<CreditCardBill[]>(`/credit-card-bills${params}`),
  })
}

export function useCreateCreditCardBill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiFetch<CreditCardBill>('/credit-card-bills', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credit-card-bills'] }),
  })
}

export function useUpdateCreditCardBill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...data }: { id: number } & Record<string, unknown>) =>
      apiFetch<CreditCardBill>(`/credit-card-bills/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credit-card-bills'] }),
  })
}

export function useDeleteCreditCardBill() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/credit-card-bills/${id}`, { method: 'DELETE' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['credit-card-bills'] }),
  })
}
