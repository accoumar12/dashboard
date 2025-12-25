/**
 * useTableSelection - Manage visible tables via URL query params
 *
 * Stores visible table names as a comma-separated list in the URL.
 * Example: ?tables=users,posts,orders
 */

import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

export function useTableSelection() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Parse visible tables from URL
  const visibleTables = useMemo(() => {
    const tablesParam = searchParams.get('tables');
    if (!tablesParam) {
      return new Set<string>();
    }
    return new Set(tablesParam.split(',').filter(Boolean));
  }, [searchParams]);

  // Update visible tables in URL
  const setVisibleTables = useCallback(
    (tables: Set<string>) => {
      if (tables.size === 0) {
        // Remove tables param if empty
        searchParams.delete('tables');
        setSearchParams(searchParams, { replace: true });
      } else {
        // Set tables as comma-separated list
        const tableList = Array.from(tables).sort().join(',');
        searchParams.set('tables', tableList);
        setSearchParams(searchParams, { replace: true });
      }
    },
    [searchParams, setSearchParams]
  );

  // Toggle a single table
  const toggleTable = useCallback(
    (tableName: string) => {
      const newTables = new Set(visibleTables);
      if (newTables.has(tableName)) {
        newTables.delete(tableName);
      } else {
        newTables.add(tableName);
      }
      setVisibleTables(newTables);
    },
    [visibleTables, setVisibleTables]
  );

  return {
    visibleTables,
    setVisibleTables,
    toggleTable,
  };
}
