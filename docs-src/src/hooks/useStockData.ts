import { useState, useEffect } from 'react';
import type { StockData } from '../types/stock';

export function useStockData() {
  const [data, setData] = useState<StockData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        // Try to fetch from data folder (relative path for GitHub Pages)
        const response = await fetch('./data/stocks.json');

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const jsonData: StockData = await response.json();
        setData(jsonData);
        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch stock data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  return { data, loading, error };
}
