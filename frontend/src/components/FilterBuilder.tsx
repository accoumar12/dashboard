/**
 * FilterBuilder - Panel for creating and managing filters.
 */

import { useState, useEffect } from 'react';
import axios from 'axios';
import type { ColumnFilter, TableInfo } from '../types';

interface FilterBuilderProps {
  tables: TableInfo[];
  filters: ColumnFilter[];
  onAddFilter: (filter: ColumnFilter) => void;
  onRemoveFilter: (index: number) => void;
}

const OPERATORS = [
  { value: 'eq', label: 'Equals' },
  { value: 'ne', label: 'Not Equals' },
  { value: 'gt', label: 'Greater Than' },
  { value: 'lt', label: 'Less Than' },
  { value: 'gte', label: 'Greater Than or Equal' },
  { value: 'lte', label: 'Less Than or Equal' },
  { value: 'contains', label: 'Contains' },
  { value: 'startswith', label: 'Starts With' },
  { value: 'endswith', label: 'Ends With' },
  { value: 'is_null', label: 'Is Null' },
  { value: 'is_not_null', label: 'Is Not Null' },
];

export function FilterBuilder({
  tables,
  filters,
  onAddFilter,
  onRemoveFilter,
}: FilterBuilderProps) {
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [selectedColumn, setSelectedColumn] = useState<string>('');
  const [selectedOperator, setSelectedOperator] = useState<string>('');
  const [columnValues, setColumnValues] = useState<(string | number | boolean)[]>([]);
  const [loadingValues, setLoadingValues] = useState(false);

  // Fetch distinct values when column and operator are selected and operator is 'eq'
  useEffect(() => {
    if (selectedTable && selectedColumn && selectedOperator === 'eq') {
      setLoadingValues(true);
      axios
        .get(`/api/column-values/${selectedTable}/${selectedColumn}`)
        .then((response) => {
          setColumnValues(response.data.values || []);
        })
        .catch((error) => {
          console.error('Failed to fetch column values:', error);
          setColumnValues([]);
        })
        .finally(() => {
          setLoadingValues(false);
        });
    } else {
      setColumnValues([]);
    }
  }, [selectedTable, selectedColumn, selectedOperator]);

  const handleAddFilter = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    const table = formData.get('table') as string;
    const column = formData.get('column') as string;
    const operator = formData.get('operator') as string;
    const value = formData.get('value') as string;

    if (!table || !column || !operator) {
      return;
    }

    // For null checks, value is not needed
    const filterValue = operator === 'is_null' || operator === 'is_not_null' ? '' : value;

    onAddFilter({
      table,
      column,
      operator,
      value: filterValue,
    });

    e.currentTarget.reset();
    setSelectedTable('');
    setSelectedColumn('');
    setSelectedOperator('');
    setColumnValues([]);
  };

  // Get columns for the selected table
  const availableColumns = selectedTable
    ? tables.find((t) => t.name === selectedTable)?.columns || []
    : [];

  // Determine if we should show value dropdown or input
  const showValueDropdown = selectedOperator === 'eq' && columnValues.length > 0;
  const valueFieldDisabled = selectedOperator === 'is_null' || selectedOperator === 'is_not_null';

  return (
    <div
      style={{
        width: '320px',
        backgroundColor: '#fff',
        borderRight: '1px solid #e5e7eb',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '20px',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: '#f9fafb',
        }}
      >
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#1f2937' }}>
          Filters ({filters.length})
        </h2>
        <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
          Filter data across tables
        </p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        {/* Active Filters */}
        {filters.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            {filters.map((filter, index) => (
              <div
                key={index}
                style={{
                  padding: '12px',
                  backgroundColor: '#eff6ff',
                  borderRadius: '6px',
                  marginBottom: '8px',
                  fontSize: '13px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, color: '#1e40af', marginBottom: '4px' }}>
                      {filter.table}.{filter.column}
                    </div>
                    <div style={{ color: '#6b7280' }}>
                      {OPERATORS.find((op) => op.value === filter.operator)?.label || filter.operator}
                      {filter.value && `: ${filter.value}`}
                    </div>
                  </div>
                  <button
                    onClick={() => onRemoveFilter(index)}
                    style={{
                      background: 'none',
                      border: 'none',
                      fontSize: '18px',
                      cursor: 'pointer',
                      color: '#9ca3af',
                      padding: '0 4px',
                      lineHeight: 1,
                    }}
                    title="Remove filter"
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add Filter Form */}
        <form onSubmit={handleAddFilter}>
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
              Table
            </label>
            <input
              type="text"
              name="table"
              required
              value={selectedTable}
              onChange={(e) => setSelectedTable(e.target.value)}
              placeholder="Type to search tables..."
              list="tables-list"
              autoComplete="off"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
              }}
            />
            <datalist id="tables-list">
              {tables.map((table) => (
                <option key={table.name} value={table.name} />
              ))}
            </datalist>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
              Column
            </label>
            <input
              type="text"
              name="column"
              required
              disabled={!selectedTable}
              value={selectedColumn}
              onChange={(e) => setSelectedColumn(e.target.value)}
              placeholder={selectedTable ? 'Type to search columns...' : 'Select table first...'}
              list={selectedTable ? 'columns-list' : undefined}
              autoComplete="off"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
                backgroundColor: !selectedTable ? '#f3f4f6' : 'white',
              }}
            />
            {selectedTable && (
              <datalist id="columns-list">
                {availableColumns.map((column) => (
                  <option key={column.name} value={column.name} />
                ))}
              </datalist>
            )}
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
              Operator
            </label>
            <select
              name="operator"
              required
              value={selectedOperator}
              onChange={(e) => setSelectedOperator(e.target.value)}
              disabled={!selectedColumn}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
                backgroundColor: !selectedColumn ? '#f3f4f6' : 'white',
              }}
            >
              <option value="">
                {selectedColumn ? 'Select operator...' : 'Select column first...'}
              </option>
              {OPERATORS.map((op) => (
                <option key={op.value} value={op.value}>
                  {op.label}
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, marginBottom: '4px', color: '#374151' }}>
              Value
            </label>
            <input
              type="text"
              name="value"
              placeholder={
                !selectedOperator
                  ? 'Select operator first...'
                  : valueFieldDisabled
                  ? ''
                  : loadingValues
                  ? 'Loading values...'
                  : showValueDropdown
                  ? 'Type to search or select...'
                  : 'Filter value'
              }
              disabled={!selectedOperator || valueFieldDisabled || loadingValues}
              list={showValueDropdown ? 'column-values-list' : undefined}
              autoComplete="off"
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                fontSize: '14px',
                backgroundColor: !selectedOperator || valueFieldDisabled || loadingValues ? '#f3f4f6' : 'white',
              }}
            />
            {showValueDropdown && (
              <datalist id="column-values-list">
                {columnValues.map((value, idx) => (
                  <option key={idx} value={String(value)} />
                ))}
              </datalist>
            )}
          </div>

          <button
            type="submit"
            style={{
              width: '100%',
              padding: '10px',
              backgroundColor: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Add Filter
          </button>
        </form>
      </div>
    </div>
  );
}
