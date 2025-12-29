/**
 * TableWidget - A draggable/resizable widget that displays a single table.
 */

import { DataTable } from './DataTable';
import { useTableData } from '../hooks/useTableData';
import type { ColumnFilter, TableInfo } from '../types';

interface TableWidgetProps {
  sessionId: string;
  tableName: string;
  tableInfo: TableInfo;
  filters: ColumnFilter[];
  onClose: () => void;
}

export function TableWidget({ sessionId, tableName, tableInfo, filters, onClose }: TableWidgetProps) {
  const { data, isLoading, error } = useTableData({
    sessionId,
    tableName,
    filters,
    enabled: true,
  });

  return (
    <div
      style={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#fff',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        overflow: 'hidden',
      }}
    >
      {/* Widget Header */}
      <div
        style={{
          padding: '12px 16px',
          backgroundColor: '#f9fafb',
          borderBottom: '1px solid #e5e7eb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'move',
        }}
        className="drag-handle"
      >
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#1f2937' }}>
            {tableName}
          </h3>
          <p style={{ margin: 0, fontSize: '12px', color: '#6b7280' }}>
            {tableInfo.columns.length} columns
            {data && ` • ${data.total} rows`}
          </p>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '20px',
            cursor: 'pointer',
            color: '#9ca3af',
            padding: '4px 8px',
            lineHeight: 1,
          }}
          title="Remove table"
        >
          ×
        </button>
      </div>

      {/* Widget Content */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {isLoading ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#6b7280',
            }}
          >
            Loading...
          </div>
        ) : error ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#dc2626',
              padding: '20px',
              textAlign: 'center',
            }}
          >
            <div>
              <p>Failed to load table data</p>
              <p style={{ fontSize: '12px', marginTop: '8px' }}>{String(error)}</p>
            </div>
          </div>
        ) : data && tableInfo ? (
          <DataTable data={data} tableInfo={tableInfo} />
        ) : null}
      </div>
    </div>
  );
}
