import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '../api/client'
import type { SimulateRequest, SimulateResponse } from '../api/types'

export function useSimulate() {
  return useMutation({
    mutationFn: (data: SimulateRequest) =>
      apiFetch<SimulateResponse>('/forecast/simulate', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}
