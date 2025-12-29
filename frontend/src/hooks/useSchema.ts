/**
 * Hook for fetching and managing database schema.
 */

import { useQuery } from '@tanstack/react-query';
import { getSchema } from '../lib/api';

export function useSchema(sessionId: string) {
  return useQuery({
    queryKey: ['schema', sessionId],
    queryFn: () => getSchema(sessionId),
    staleTime: 5 * 60 * 1000, // Schema doesn't change often, cache for 5 minutes
    refetchOnWindowFocus: false,
  });
}
