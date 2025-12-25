import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useMemo } from 'react';
import type { Layout } from 'react-grid-layout/legacy';
import { FilterBuilder } from './components/FilterBuilder';
import { Sidebar } from './components/Sidebar';
import { TableWidget } from './components/TableWidget';
import { WidgetGrid } from './components/WidgetGrid';
import type { WidgetConfig } from './components/WidgetGrid';
import { useFilters } from './hooks/useFilters';
import { useSchema } from './hooks/useSchema';
import { useTableSelection } from './hooks/useTableSelection';
import { getDefaultWidgetSize } from './lib/gridUtils';
import './App.css';

const queryClient = new QueryClient();

function Dashboard() {
  const { data: schema, isLoading: schemaLoading, error: schemaError } = useSchema();
  const { visibleTables, toggleTable } = useTableSelection();
  const { filters, addFilter, removeFilter } = useFilters();

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
          Make sure PostgreSQL is running and the database contains tables.
          <br />
          Or the SQLite playground database is available.
        </p>
      </div>
    );
  }

  if (!schema || schema.tables.length === 0) {
    return (
      <div className="empty-state">
        <h2>No tables found</h2>
        <p>Your database doesn't contain any tables yet.</p>
        <p style={{ marginTop: '12px' }}>
          To load sample data, run:
          <br />
          <code>python scripts/create_playground_db.py</code>
        </p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <FilterBuilder
        tables={schema.tables}
        filters={filters}
        onAddFilter={addFilter}
        onRemoveFilter={removeFilter}
      />

      <Sidebar
        tables={schema.tables}
        visibleTables={visibleTables}
        onToggleTable={handleToggleTable}
      />

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
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="App">
        <header className="app-header">
          <h1>SQL Dashboard</h1>
          <p className="subtitle">Interactive database visualization with draggable tables</p>
        </header>
        <Dashboard />
      </div>
    </QueryClientProvider>
  );
}

export default App;
