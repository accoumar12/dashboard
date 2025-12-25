/**
 * Hook for fetching and managing database schema.
 */

import { useQuery } from '@tanstack/react-query';
import { getSchema } from '../lib/api';

export function useSchema() {
  return useQuery({
    queryKey: ['schema'],
    queryFn: getSchema,
    staleTime: 5 * 60 * 1000, // Schema doesn't change often, cache for 5 minutes
    refetchOnWindowFocus: false,
  });
}
