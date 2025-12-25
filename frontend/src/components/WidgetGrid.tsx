/**
 * WidgetGrid - Manages the grid layout for table widgets.
 */

import { Responsive, WidthProvider } from 'react-grid-layout/legacy';
import type { Layout } from 'react-grid-layout/legacy';

const ResponsiveGridLayout = WidthProvider(Responsive);

export type WidgetConfig = {
  i: string; // unique id (table name)
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  minH?: number;
}

interface WidgetGridProps {
  widgets: WidgetConfig[];
  onLayoutChange: (layout: Layout) => void;
  children: React.ReactNode;
}

export function WidgetGrid({ widgets, onLayoutChange, children }: WidgetGridProps) {
  return (
    <ResponsiveGridLayout
      className="layout"
      layouts={{
        lg: widgets,
        md: widgets,
        sm: widgets,
        xs: widgets,
        xxs: widgets
      }}
      breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
      cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
      rowHeight={100}
      onLayoutChange={onLayoutChange}
      draggableHandle=".drag-handle"
      compactType="vertical"
      preventCollision={false}
      isDraggable={true}
      isResizable={true}
      containerPadding={[0, 0]}
      margin={[16, 16]}
    >
      {children}
    </ResponsiveGridLayout>
  );
}
