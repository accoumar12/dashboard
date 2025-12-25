/**
 * useFilters - Manage filters via URL query params
 *
 * Stores filters as URL-encoded JSON in the URL.
 * Example: ?filters=[{"table":"users","column":"name","operator":"contains","value":"john"}]
 */

import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { ColumnFilter } from '../types';

export function useFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Parse filters from URL
  const filters = useMemo<ColumnFilter[]>(() => {
    const filtersParam = searchParams.get('filters');
    if (!filtersParam) {
      return [];
    }

    try {
      const decoded = JSON.parse(decodeURIComponent(filtersParam));
      if (Array.isArray(decoded)) {
        return decoded;
      }
      return [];
    } catch {
      return [];
    }
  }, [searchParams]);

  // Update filters in URL
  const setFilters = useCallback(
    (newFilters: ColumnFilter[]) => {
      if (newFilters.length === 0) {
        // Remove filters param if empty
        searchParams.delete('filters');
      } else {
        // Encode filters as JSON
        const encoded = encodeURIComponent(JSON.stringify(newFilters));
        searchParams.set('filters', encoded);
      }
      setSearchParams(searchParams, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  // Add a filter
  const addFilter = useCallback(
    (filter: ColumnFilter) => {
      setFilters([...filters, filter]);
    },
    [filters, setFilters]
  );

  // Remove a filter by index
  const removeFilter = useCallback(
    (index: number) => {
      setFilters(filters.filter((_, i) => i !== index));
    },
    [filters, setFilters]
  );

  // Clear all filters
  const clearFilters = useCallback(() => {
    setFilters([]);
  }, [setFilters]);

  return {
    filters,
    setFilters,
    addFilter,
    removeFilter,
    clearFilters,
  };
}
