import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import type { Layout } from 'react-grid-layout/legacy';
import { Sidebar } from './components/Sidebar';
import { TableWidget } from './components/TableWidget';
import { WidgetGrid } from './components/WidgetGrid';
import type { WidgetConfig } from './components/WidgetGrid';
import { useSchema } from './hooks/useSchema';
import { findNextPosition, getDefaultWidgetSize } from './lib/gridUtils';
import './App.css';

const queryClient = new QueryClient();

function Dashboard() {
  const { data: schema, isLoading: schemaLoading, error: schemaError } = useSchema();

  const [visibleTables, setVisibleTables] = useState<Set<string>>(new Set());
  const [widgets, setWidgets] = useState<WidgetConfig[]>([]);

  const handleToggleTable = (tableName: string) => {
    if (visibleTables.has(tableName)) {
      // Remove table
      setVisibleTables((prev) => {
        const next = new Set(prev);
        next.delete(tableName);
        return next;
      });
      setWidgets((prev) => prev.filter((w) => w.i !== tableName));
    } else {
      // Add table
      setVisibleTables((prev) => new Set(prev).add(tableName));

      const position = findNextPosition(widgets);
      const size = getDefaultWidgetSize();

      const newWidget: WidgetConfig = {
        i: tableName,
        x: position.x,
        y: position.y,
        w: size.w,
        h: size.h,
        minW: 3,
        minH: 3,
      };

      setWidgets((prev) => [...prev, newWidget]);
    }
  };

  const handleLayoutChange = (layout: Layout) => {
    // Update widget positions when user drags/resizes
    setWidgets((prev) =>
      prev.map((widget) => {
        const layoutItem = layout.find((l) => l.i === widget.i);
        if (layoutItem) {
          return {
            ...widget,
            x: layoutItem.x,
            y: layoutItem.y,
            w: layoutItem.w,
            h: layoutItem.h,
          };
        }
        return widget;
      })
    );
  };

  const handleCloseWidget = (tableName: string) => {
    handleToggleTable(tableName);
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
