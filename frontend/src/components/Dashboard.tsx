/**
 * Main dashboard component for displaying database tables and filters.
 */

import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Layout } from 'react-grid-layout/legacy';
import { Zap, SlidersHorizontal } from 'lucide-react';
import { AnimatedDogLogo } from './AnimatedDogLogo';
import { FilterBuilder } from './FilterBuilder';
import { Sidebar } from './Sidebar';
import { TableWidget } from './TableWidget';
import { WidgetGrid } from './WidgetGrid';
import type { WidgetConfig } from './WidgetGrid';
import { useFilters } from '../hooks/useFilters';
import { useSchema } from '../hooks/useSchema';
import { useTableSelection } from '../hooks/useTableSelection';
import { getDefaultWidgetSize } from '../lib/gridUtils';

interface DashboardProps {
  sessionId: string;
}

export function Dashboard({ sessionId }: DashboardProps) {
  const navigate = useNavigate();
  const { data: schema, isLoading: schemaLoading, error: schemaError } = useSchema(sessionId);
  const { visibleTables, toggleTable } = useTableSelection();
  const { filters, addFilter, removeFilter } = useFilters();
  const [showTables, setShowTables] = useState(true);
  const [showFilters, setShowFilters] = useState(true);

  // Generate widgets from visible tables (auto-positioned)
  const widgets = useMemo<WidgetConfig[]>(() => {
    const size = getDefaultWidgetSize();
    const gridCols = 12;
    const widgetCols = size.w;
    const widgetsPerRow = Math.floor(gridCols / widgetCols);

    return Array.from(visibleTables).map((tableName, index) => {
      const row = Math.floor(index / widgetsPerRow);
      const col = index % widgetsPerRow;

      return {
        i: tableName,
        x: col * widgetCols,
        y: row * size.h,
        w: widgetCols,
        h: size.h,
        minW: 3,
        minH: 3,
      };
    });
  }, [visibleTables]);

  const handleToggleTable = (tableName: string) => {
    toggleTable(tableName);
  };

  const handleLayoutChange = (_layout: Layout) => {
    // Layout changes are not persisted to URL
    // Widgets are auto-positioned based on visible tables
  };

  const handleCloseWidget = (tableName: string) => {
    toggleTable(tableName);
  };

  if (schemaLoading) {
    return (
      <div className="loading">
        <p>Loading database schema...</p>
      </div>
    );
  }

  if (schemaError) {
    return (
      <div className="error">
        <h2>Failed to load schema</h2>
        <p>{String(schemaError)}</p>
        <p style={{ marginTop: '12px', color: '#666' }}>
          Make sure the database session is valid.
          <br />
          Sessions expire after 7 days of inactivity.
        </p>
      </div>
    );
  }

  if (!schema || schema.tables.length === 0) {
    return (
      <div className="empty-state">
        <h2>No tables found</h2>
        <p>This database doesn't contain any tables.</p>
      </div>
    );
  }

  return (
    <div className="App">
      {/* Header with toggle buttons */}
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', width: '100%', height: '100%' }}>
          {/* Home button with dog logo */}
          <div
            onClick={() => navigate('/')}
            style={{
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              flexShrink: 0,
            }}
            title="Go to home page"
          >
            <AnimatedDogLogo />
          </div>

          <div style={{ flex: 1 }}>
            <h1 style={{ margin: 0 }}>SQL Dashboard</h1>
            <p className="subtitle" style={{ margin: 0 }}>
              Interactive database visualization with draggable tables
              {sessionId !== 'playground' && ' • Session: ' + sessionId.substring(0, 8)}
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setShowTables(!showTables)}
              style={{
                padding: '8px 16px',
                backgroundColor: showTables ? '#667eea' : '#fff',
                color: showTables ? '#fff' : '#374151',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
              title={showTables ? 'Hide tables panel' : 'Show tables panel'}
            >
              <Zap size={16} />
              Tables
            </button>
            <button
              onClick={() => setShowFilters(!showFilters)}
              style={{
                padding: '8px 16px',
                backgroundColor: showFilters ? '#667eea' : '#fff',
                color: showFilters ? '#fff' : '#374151',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
              }}
              title={showFilters ? 'Hide filters panel' : 'Show filters panel'}
            >
              <SlidersHorizontal size={16} />
              Filters
            </button>
          </div>
        </div>
      </header>

      <div className="dashboard">
        {/* Tables panel (on the left) */}
        {showTables && (
          <Sidebar
            tables={schema.tables}
            visibleTables={visibleTables}
            onToggleTable={handleToggleTable}
          />
        )}

        {/* Filters panel (after tables) */}
        {showFilters && (
          <FilterBuilder
            tables={schema.tables}
            filters={filters}
            onAddFilter={addFilter}
            onRemoveFilter={removeFilter}
          />
        )}

        <div className="grid-container">
          {widgets.length === 0 ? (
            <div className="empty-state">
              <h2>No tables selected</h2>
              <p>Select tables from the sidebar to display them here</p>
              <p style={{ marginTop: '12px', fontSize: '14px', color: '#6b7280' }}>
                You can select multiple tables and arrange them by dragging
              </p>
            </div>
          ) : (
            <WidgetGrid widgets={widgets} onLayoutChange={handleLayoutChange}>
              {widgets.map((widget) => {
                const tableInfo = schema.tables.find((t) => t.name === widget.i);
                if (!tableInfo) return null;

                return (
                  <div key={widget.i}>
                    <TableWidget
                      sessionId={sessionId}
                      tableName={widget.i}
                      tableInfo={tableInfo}
                      filters={filters}
                      onClose={() => handleCloseWidget(widget.i)}
                    />
                  </div>
                );
              })}
            </WidgetGrid>
          )}
        </div>
      </div>
    </div>
  );
}
