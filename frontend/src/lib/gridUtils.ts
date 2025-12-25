/**
 * Utility functions for grid layout management.
 */

import type { WidgetConfig } from '../components/WidgetGrid';

/**
 * Find the next available position in the grid for a new widget.
 */
export function findNextPosition(existingWidgets: WidgetConfig[]): { x: number; y: number } {
  if (existingWidgets.length === 0) {
    return { x: 0, y: 0 };
  }

  // Find the widget with the highest y position
  const maxY = Math.max(...existingWidgets.map((w) => w.y + w.h));

  // Try to place in the next row
  return { x: 0, y: maxY };
}

/**
 * Create default widget dimensions.
 */
export function getDefaultWidgetSize(): { w: number; h: number } {
  return {
    w: 6, // Half width on large screens
    h: 4, // 4 rows tall
  };
}
