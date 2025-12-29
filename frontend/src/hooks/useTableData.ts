/**
 * Hook for fetching table data with filters and pagination.
 */

import { useQuery } from '@tanstack/react-query';
import { queryTable } from '../lib/api';
import type { ColumnFilter, SortConfig } from '../types';

interface UseTableDataOptions {
  sessionId: string;
  tableName: string;
  filters?: ColumnFilter[];
  sort?: SortConfig;
  offset?: number;
  limit?: number;
  enabled?: boolean;
}

export function useTableData({
  sessionId,
  tableName,
  filters = [],
  sort,
  offset = 0,
  limit = 50,
  enabled = true,
}: UseTableDataOptions) {
  return useQuery({
    queryKey: ['table', sessionId, tableName, filters, sort, offset, limit],
    queryFn: () =>
      queryTable(sessionId, {
        table: tableName,
        filters,
        sort,
        offset,
        limit,
      }),
    enabled: enabled && !!tableName && !!sessionId,
    staleTime: 30 * 1000, // Data is somewhat fresh for 30 seconds
  });
}
