/**
 * DataTable component for displaying query results.
 */

import type { QueryResponse, TableInfo } from '../types';

interface DataTableProps {
  data: QueryResponse;
  tableInfo: TableInfo;
}

export function DataTable({ data, tableInfo }: DataTableProps) {
  if (!data || !data.data || data.data.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        No data available
      </div>
    );
  }

  return (
    <div style={{
      overflowX: 'auto',
      overflowY: 'auto',
      flex: 1,
      padding: '16px',
      backgroundColor: '#ffffff'
    }}>
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: '14px',
        border: '1px solid #ddd',
        color: '#1f2937'
      }}>
        <thead>
          <tr style={{ backgroundColor: '#f5f5f5' }}>
            {tableInfo.columns.map((col) => (
              <th
                key={col.name}
                style={{
                  padding: '12px 8px',
                  textAlign: 'left',
                  borderBottom: '2px solid #ddd',
                  fontWeight: 600,
                  color: '#1f2937'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#1f2937' }}>
                  {col.name}
                  {col.primary_key && (
                    <span style={{ fontSize: '10px', color: '#888' }}>🔑</span>
                  )}
                </div>
                <div style={{ fontSize: '11px', color: '#666', fontWeight: 'normal' }}>
                  {col.type}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.data.map((row, idx) => (
            <tr
              key={idx}
              style={{
                backgroundColor: idx % 2 === 0 ? '#fff' : '#f9f9f9',
              }}
            >
              {tableInfo.columns.map((col) => (
                <td
                  key={col.name}
                  style={{
                    padding: '10px 8px',
                    borderBottom: '1px solid #eee',
                    color: '#1f2937'
                  }}
                >
                  {row[col.name] === null ? (
                    <span style={{ color: '#999', fontStyle: 'italic' }}>NULL</span>
                  ) : typeof row[col.name] === 'boolean' ? (
                    row[col.name] ? '✓' : '✗'
                  ) : (
                    String(row[col.name])
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{
        padding: '12px',
        textAlign: 'center',
        fontSize: '13px',
        color: '#666',
        borderTop: '1px solid #eee'
      }}>
        Showing {data.offset + 1} - {Math.min(data.offset + data.limit, data.total)} of {data.total} rows
      </div>
    </div>
  );
}
