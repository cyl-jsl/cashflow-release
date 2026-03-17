import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { Transaction, ImportResponse } from '../api/types'

export function useTransactions(params?: { credit_card_id?: number; source_file?: string }) {
  const searchParams = new URLSearchParams()
  if (params?.credit_card_id) searchParams.set('credit_card_id', String(params.credit_card_id))
  if (params?.source_file) searchParams.set('source_file', params.source_file)
  const qs = searchParams.toString()

  return useQuery({
    queryKey: ['transactions', params],
    queryFn: () => apiFetch<Transaction[]>(`/transactions${qs ? `?${qs}` : ''}`),
  })
}

export function useImportTransactions() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (args: {
      file: File
      dateColumn: string
      descriptionColumn: string
      amountColumn: string
      creditCardId?: number
      accountId?: number
    }) => {
      const formData = new FormData()
      formData.append('file', args.file)
      formData.append('date_column', args.dateColumn)
      formData.append('description_column', args.descriptionColumn)
      formData.append('amount_column', args.amountColumn)
      if (args.creditCardId) formData.append('credit_card_id', String(args.creditCardId))
      if (args.accountId) formData.append('account_id', String(args.accountId))

      const res = await fetch('/api/v1/transactions/import', {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err?.error?.message || `匯入失敗: ${res.status}`)
      }
      const json = await res.json()
      return json.data as ImportResponse
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['transactions'] }),
  })
}

export function useDeleteTransactions() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (sourceFile: string) =>
      apiFetch<{ deleted: number }>(`/transactions?source_file=${encodeURIComponent(sourceFile)}`, {
        method: 'DELETE',
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['transactions'] }),
  })
}
