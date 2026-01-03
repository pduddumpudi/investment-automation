import { useState } from 'react';
import type { Stock } from '../types/stock';

interface ThesisGeneratorProps {
  stock: Stock;
  onThesisUpdate: (ticker: string, thesis: string) => void;
}

export function ThesisGenerator({ stock, onThesisUpdate }: ThesisGeneratorProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const thesis = stock.thesis?.trim() || '';

  const handleGenerate = async () => {
    if (isLoading) return;
    setError(null);

    let password = sessionStorage.getItem('thesis_password');
    if (!password) {
      password = window.prompt('Enter thesis password') || '';
      if (!password) {
        return;
      }
      sessionStorage.setItem('thesis_password', password);
    }

    try {
      setIsLoading(true);
      const response = await fetch('/api/thesis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ticker: stock.ticker,
          company_name: stock.company_name,
          investor_names: stock.dataroma_data.investors.map(inv => inv.name),
          password,
        }),
      });

      const payload = await response.json();
      if (!response.ok || !payload?.success) {
        const message = payload?.error || 'Failed to generate thesis';
        setError(message);
        return;
      }

      onThesisUpdate(stock.ticker, payload.thesis || '');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate thesis');
    } finally {
      setIsLoading(false);
    }
  };

  if (thesis) {
    const displayText = thesis.length > 80 ? `${thesis.slice(0, 80)}...` : thesis;
    return (
      <span className="truncate max-w-[220px] block text-sm text-gray-600" title={thesis}>
        {displayText}
      </span>
    );
  }

  return (
    <div className="flex flex-col items-start gap-1">
      <button
        type="button"
        onClick={handleGenerate}
        disabled={isLoading}
        className="px-3 py-1 text-xs bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-60"
      >
        {isLoading ? 'Generating...' : 'Generate'}
      </button>
      {error && <span className="text-xs text-red-600">{error}</span>}
    </div>
  );
}
