import { useState, useEffect } from 'react';
import type { ColumnConfig } from '../types/stock';
import { DEFAULT_COLUMNS } from '../types/stock';

const STORAGE_KEY = 'investment-dashboard-columns';

function getColumnsFromUrl(): string[] | null {
  const params = new URLSearchParams(window.location.search);
  const cols = params.get('cols');
  if (cols) {
    return cols.split(',').map(c => c.trim());
  }
  return null;
}

function getColumnsFromStorage(): ColumnConfig[] | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      return JSON.parse(stored);
    }
  } catch (e) {
    console.warn('Failed to load column preferences from localStorage');
  }
  return null;
}

export function useColumnPreferences() {
  const [columns, setColumns] = useState<ColumnConfig[]>(() => {
    // Priority: URL params > localStorage > defaults
    const urlCols = getColumnsFromUrl();
    if (urlCols) {
      return DEFAULT_COLUMNS.map(col => ({
        ...col,
        visible: urlCols.includes(col.id),
      }));
    }

    const storedCols = getColumnsFromStorage();
    if (storedCols) {
      return storedCols;
    }

    return DEFAULT_COLUMNS;
  });

  // Save to localStorage when columns change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(columns));
  }, [columns]);

  const toggleColumn = (columnId: string) => {
    setColumns(prev =>
      prev.map(col =>
        col.id === columnId ? { ...col, visible: !col.visible } : col
      )
    );
  };

  const setColumnVisibility = (columnId: string, visible: boolean) => {
    setColumns(prev =>
      prev.map(col =>
        col.id === columnId ? { ...col, visible } : col
      )
    );
  };

  const resetToDefaults = () => {
    setColumns(DEFAULT_COLUMNS);
  };

  const getShareableUrl = () => {
    const visibleCols = columns.filter(c => c.visible).map(c => c.id);
    const url = new URL(window.location.href);
    url.searchParams.set('cols', visibleCols.join(','));
    return url.toString();
  };

  const visibleColumns = columns.filter(c => c.visible);

  return {
    columns,
    visibleColumns,
    toggleColumn,
    setColumnVisibility,
    resetToDefaults,
    getShareableUrl,
  };
}
