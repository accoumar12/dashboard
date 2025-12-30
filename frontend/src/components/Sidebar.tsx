/**
 * Sidebar - Table selection panel with checkboxes.
 */

import type { TableInfo } from '../types';

interface SidebarProps {
  tables: TableInfo[];
  visibleTables: Set<string>;
  onToggleTable: (tableName: string) => void;
}

export function Sidebar({ tables, visibleTables, onToggleTable }: SidebarProps) {
  return (
    <div
      style={{
        width: '280px',
        backgroundColor: '#fff',
        borderRight: '1px solid #e5e7eb',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '20px',
          borderBottom: '1px solid #e5e7eb',
          backgroundColor: '#f9fafb',
        }}
      >
        <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600, color: '#1f2937' }}>
          Tables ({tables.length})
        </h2>
        <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
          Select tables to display
        </p>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
        {tables.map((table) => {
          const isVisible = visibleTables.has(table.name);
          return (
            <label
              key={table.name}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '12px',
                cursor: 'pointer',
                borderRadius: '6px',
                transition: 'background-color 0.15s',
                backgroundColor: isVisible ? '#eff6ff' : 'transparent',
              }}
              onMouseEnter={(e) => {
                if (!isVisible) {
                  e.currentTarget.style.backgroundColor = '#f9fafb';
                }
              }}
              onMouseLeave={(e) => {
                if (!isVisible) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }
              }}
            >
              <input
                type="checkbox"
                checked={isVisible}
                onChange={() => onToggleTable(table.name)}
                style={{
                  width: '18px',
                  height: '18px',
                  marginRight: '12px',
                  cursor: 'pointer',
                  accentColor: '#000000',
                }}
              />
              <div style={{ flex: 1 }}>
                <div
                  style={{
                    fontSize: '14px',
                    fontWeight: isVisible ? 600 : 500,
                    color: '#1f2937',
                    marginBottom: '2px',
                  }}
                >
                  {table.name}
                </div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>
                  {table.columns.length} columns
                </div>
              </div>
            </label>
          );
        })}
      </div>
    </div>
  );
}
