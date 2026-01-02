/**
 * Main dashboard component for displaying database tables and filters.
 */

import { useMemo, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, SlidersHorizontal } from 'lucide-react';
import { AnimatedDogLogo } from './AnimatedDogLogo';
import { FilterBuilder } from './FilterBuilder';
import { Sidebar } from './Sidebar';
import { TableWidget } from './TableWidget';
import { WidgetGrid } from './WidgetGrid';
import { ShortcutsModal } from './ShortcutsModal';
import { CircleHelpIcon } from './CircleHelpIcon';
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
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  // Keyboard shortcut listener for "?"
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Check if "?" is pressed (Shift + / on most keyboards)
      if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        // Don't trigger if user is typing in an input
        const target = e.target as HTMLElement;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
          return;
        }
        e.preventDefault();
        setShowShortcuts((prev) => !prev);
      }
      // Also listen for Escape to close modal
      if (e.key === 'Escape' && showShortcuts) {
        setShowShortcuts(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showShortcuts]);

  // Auto-hide toast after 3 seconds
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

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

  const handleLayoutChange = () => {
    // Layout changes are not persisted to URL
    // Widgets are auto-positioned based on visible tables
  };

  const handleCloseWidget = (tableName: string) => {
    toggleTable(tableName);
  };

  const handleCellClick = (tableName: string, columnName: string, value: string | number | boolean | null) => {
    // Don't add filter for NULL values
    if (value === null) {
      return;
    }

    // Add equals filter
    addFilter({
      table: tableName,
      column: columnName,
      operator: 'eq',
      value: String(value),
    });

    // Show toast notification
    setToast(`Filter added: ${tableName}.${columnName} = ${value}`);
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

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              onClick={() => setShowTables(!showTables)}
              style={{
                padding: '8px 16px',
                backgroundColor: showTables ? '#fff' : '#000000',
                color: showTables ? '#374151' : '#fff',
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
              {showTables ? 'Hide Tables' : 'Show Tables'}
            </button>
            <button
              onClick={() => setShowFilters(!showFilters)}
              style={{
                padding: '8px 16px',
                backgroundColor: showFilters ? '#fff' : '#000000',
                color: showFilters ? '#374151' : '#fff',
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
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>
          </div>

          {/* GitHub Link - far right */}
          <a
            href="https://github.com/accoumar12/dashboard"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              padding: '8px 12px',
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              color: '#fff',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              textDecoration: 'none',
              transition: 'all 0.2s',
              marginLeft: 'auto',
            }}
            title="View on GitHub"
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.25)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.15)';
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
            GitHub
          </a>
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
            sessionId={sessionId}
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
                      onCellClick={handleCellClick}
                    />
                  </div>
                );
              })}
            </WidgetGrid>
          )}
        </div>
      </div>

      {/* Shortcuts button - bottom right */}
      <button
        onClick={() => setShowShortcuts(true)}
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: '#000000',
          color: '#ffffff',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          transition: 'all 0.2s',
          zIndex: 100,
        }}
        title="Keyboard shortcuts (?)"
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.1)';
          e.currentTarget.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.15)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
        }}
      >
        <CircleHelpIcon size={32} />
      </button>

      {/* Shortcuts modal */}
      <ShortcutsModal isOpen={showShortcuts} onClose={() => setShowShortcuts(false)} />

      {/* Toast notification */}
      {toast && (
        <div
          style={{
            position: 'fixed',
            bottom: '80px',
            right: '20px',
            backgroundColor: '#1f2937',
            color: '#ffffff',
            padding: '12px 16px',
            borderRadius: '8px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            fontSize: '14px',
            zIndex: 999,
            maxWidth: '400px',
            animation: 'slideIn 0.2s ease-out',
          }}
        >
          {toast}
        </div>
      )}
    </div>
  );
}
