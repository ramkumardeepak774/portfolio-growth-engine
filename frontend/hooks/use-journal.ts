import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { journalService } from "@/services/market-data"
import type { CreateJournalEntryRequest } from "@/types"

export const JOURNAL_KEYS = {
  all: ["journal"] as const,
  entries: (params?: object) => ["journal", "entries", params] as const,
  entry: (id: string) => ["journal", "entry", id] as const,
}

export function useJournalEntries(params?: { symbol?: string; action?: string }) {
  return useQuery({
    queryKey: JOURNAL_KEYS.entries(params),
    queryFn: () => journalService.getEntries(params),
    staleTime: 2 * 60 * 1000,
    retry: 2,
  })
}

export function useCreateJournalEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: CreateJournalEntryRequest) => journalService.createEntry(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: JOURNAL_KEYS.all })
    },
  })
}

export function useReviewEntry() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      ...payload
    }: {
      id: string
      outcome: string
      what_went_right?: string
      what_went_wrong?: string
      bias_identified?: string
      lesson_learned?: string
      rating?: number
    }) => journalService.reviewEntry(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: JOURNAL_KEYS.all })
    },
  })
}
