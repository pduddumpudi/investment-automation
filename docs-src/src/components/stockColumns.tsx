import type { ColumnDef } from '@tanstack/react-table';
import type { Stock } from '../types/stock';
import { ThesisGenerator } from './ThesisGenerator';

interface StockColumnsOptions {
  onThesisUpdate: (ticker: string, thesis: string) => void;
}

function formatNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === 'N/A') return 'N/A';
  if (typeof value === 'string') return value;
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function formatMarketCap(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === 'N/A') return 'N/A';
  if (typeof value === 'string') return value;
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
}

function formatPercent(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === 'N/A') return 'N/A';
  if (typeof value === 'string') return value;
  return `${formatNumber(value)}%`;
}

function getPEColorClass(pe: number | string): string {
  if (typeof pe !== 'number') return '';
  if (pe < 0) return 'text-gray-400';
  if (pe < 15) return 'text-green-600 font-semibold';
  if (pe < 25) return 'text-yellow-600';
  return 'text-red-600';
}

function getDistanceClass(value: number | string, mode: 'above' | 'below'): string {
  if (typeof value !== 'number') return '';
  if (mode === 'above' && value < 10) return 'text-green-600 font-semibold';
  if (mode === 'below' && value < 10) return 'text-red-600 font-semibold';
  return '';
}

function getActivityBadgeClass(activity: string): string {
  const action = activity.toLowerCase();
  if (action === 'new' || action === 'buy') return 'bg-green-100 text-green-800';
  if (action === 'add') return 'bg-blue-100 text-blue-800';
  if (action === 'sell') return 'bg-red-100 text-red-800';
  if (action === 'reduce') return 'bg-orange-100 text-orange-800';
  return 'bg-gray-100 text-gray-600';
}

function coerceNumber(value: unknown): number | null {
  if (value === null || value === undefined) return null;
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  if (typeof value === 'string') {
    if (value.trim() === '' || value === 'N/A') return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function getStockColumns({ onThesisUpdate }: StockColumnsOptions): ColumnDef<Stock>[] {
  return [
    {
      id: 'expander',
      header: () => null,
      cell: ({ row }) => (
        <button
          onClick={() => row.toggleExpanded()}
          className="p-1 hover:bg-gray-100 rounded"
        >
          <svg
            className={`w-5 h-5 transition-transform ${row.getIsExpanded() ? 'rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      ),
      size: 40,
      enableSorting: false,
    },
    {
      id: 'ticker',
      accessorKey: 'ticker',
      header: 'Ticker',
      cell: ({ row }) => (
        <span className="font-bold text-blue-600">{row.original.ticker}</span>
      ),
    },
    {
      id: 'company_name',
      accessorKey: 'company_name',
      header: 'Company',
      cell: ({ row }) => (
        <span className="truncate max-w-[200px] block" title={row.original.company_name}>
          {row.original.company_name}
        </span>
      ),
    },
    {
      id: 'pe_ratio',
      accessorFn: (row) => row.fundamentals?.pe_ratio,
      header: 'PE Ratio',
      cell: ({ row }) => {
        const pe = row.original.fundamentals?.pe_ratio;
        return (
          <span className={getPEColorClass(pe)}>
            {formatNumber(pe)}
          </span>
        );
      },
      filterFn: (row, columnId, filterValue: string) => {
        if (!filterValue) return true;
        const value = coerceNumber(row.getValue(columnId));
        if (filterValue === 'na') return value === null;
        if (value === null) return false;
        if (filterValue === 'lt10') return value < 10;
        if (filterValue === '10-15') return value >= 10 && value < 15;
        if (filterValue === '15-25') return value >= 15 && value < 25;
        if (filterValue === '25-40') return value >= 25 && value < 40;
        if (filterValue === 'gt40') return value >= 40;
        return true;
      },
    },
    {
      id: 'pb_ratio',
      accessorFn: (row) => row.fundamentals?.pb_ratio,
      header: 'PB Ratio',
      cell: ({ row }) => formatNumber(row.original.fundamentals?.pb_ratio),
    },
    {
      id: 'week_52_low',
      accessorFn: (row) => row.fundamentals?.week_52_low,
      header: '52W Low',
      cell: ({ row }) => {
        const low = row.original.fundamentals?.week_52_low;
        return low !== 'N/A' ? `$${formatNumber(low)}` : 'N/A';
      },
    },
    {
      id: 'week_52_high',
      accessorFn: (row) => row.fundamentals?.week_52_high,
      header: '52W High',
      cell: ({ row }) => {
        const high = row.original.fundamentals?.week_52_high;
        return high !== 'N/A' ? `$${formatNumber(high)}` : 'N/A';
      },
    },
    {
      id: 'pct_above_52w_low',
      accessorFn: (row) => row.fundamentals?.pct_above_52w_low,
      header: '% Above Low',
      cell: ({ row }) => {
        const value = row.original.fundamentals?.pct_above_52w_low;
        return (
          <span className={getDistanceClass(value, 'above')}>
            {formatPercent(value)}
          </span>
        );
      },
      filterFn: (row, columnId, filterValue: string) => {
        if (!filterValue) return true;
        const value = coerceNumber(row.getValue(columnId));
        if (value === null) return false;
        if (filterValue === 'lt5') return value < 5;
        if (filterValue === '5-15') return value >= 5 && value < 15;
        if (filterValue === '15-30') return value >= 15 && value < 30;
        if (filterValue === 'gt30') return value >= 30;
        return true;
      },
    },
    {
      id: 'pct_below_52w_high',
      accessorFn: (row) => row.fundamentals?.pct_below_52w_high,
      header: '% Below High',
      cell: ({ row }) => {
        const value = row.original.fundamentals?.pct_below_52w_high;
        return (
          <span className={getDistanceClass(value, 'below')}>
            {formatPercent(value)}
          </span>
        );
      },
    },
    {
      id: 'sources',
      accessorFn: (row) => row.sources.join(', '),
      header: 'Sources',
      cell: ({ row }) => (
        <div className="flex gap-1">
          {row.original.sources.includes('Dataroma') && (
            <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
              Dataroma
            </span>
          )}
          {row.original.sources.includes('Substack') && (
            <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
              Substack
            </span>
          )}
        </div>
      ),
      filterFn: (row, _columnId, filterValue: string[]) => {
        if (!filterValue || filterValue.length === 0) return true;
        return filterValue.some(source => row.original.sources.includes(source as 'Dataroma' | 'Substack'));
      },
    },
    {
      id: 'investors',
      accessorFn: (row) => row.investor_count,
      header: 'Investors',
      cell: ({ row }) => {
        const count = row.original.investor_count;
        if (count === 0) return '-';
        const names = row.original.dataroma_data.investors.slice(0, 3).map(i => i.name);
        const displayText = count > 3 ? `${names.join(', ')} +${count - 3}` : names.join(', ');
        return (
          <span className="text-sm" title={row.original.dataroma_data.investors.map(i => i.name).join(', ')}>
            <span className="font-semibold text-blue-600">{count}</span>
            <span className="text-gray-500 ml-1 truncate max-w-[150px] inline-block align-bottom">
              ({displayText})
            </span>
          </span>
        );
      },
      filterFn: (row, columnId, filterValue: string) => {
        if (!filterValue) return true;
        const value = coerceNumber(row.getValue(columnId));
        if (value === null) return false;
        if (filterValue === '1') return value === 1;
        if (filterValue === '2-3') return value >= 2 && value <= 3;
        if (filterValue === '4-5') return value >= 4 && value <= 5;
        if (filterValue === '6+') return value >= 6;
        return true;
      },
    },
    {
      id: 'activity',
      accessorKey: 'aggregate_activity',
      header: 'Activity',
      cell: ({ row }) => {
        const activity = row.original.aggregate_activity;
        if (activity === 'Hold') return <span className="text-gray-400">-</span>;
        return (
          <span className={`px-2 py-1 text-xs rounded-full ${getActivityBadgeClass(activity)}`}>
            {activity}
          </span>
        );
      },
      filterFn: (row, columnId, filterValue: string[]) => {
        if (!filterValue || filterValue.length === 0) return true;
        const value = String(row.getValue(columnId) || '');
        return filterValue.includes(value);
      },
    },
    {
      id: 'market_cap',
      accessorFn: (row) => row.fundamentals?.market_cap,
      header: 'Market Cap',
      cell: ({ row }) => formatMarketCap(row.original.fundamentals?.market_cap),
    },
    {
      id: 'peg_ratio',
      accessorFn: (row) => row.fundamentals?.peg_ratio,
      header: 'PEG',
      cell: ({ row }) => formatNumber(row.original.fundamentals?.peg_ratio),
    },
    {
      id: 'forward_pe',
      accessorFn: (row) => row.fundamentals?.forward_pe,
      header: 'Fwd PE',
      cell: ({ row }) => formatNumber(row.original.fundamentals?.forward_pe),
    },
    {
      id: 'total_cash',
      accessorFn: (row) => row.fundamentals?.total_cash,
      header: 'Cash',
      cell: ({ row }) => formatMarketCap(row.original.fundamentals?.total_cash),
    },
    {
      id: 'total_debt',
      accessorFn: (row) => row.fundamentals?.total_debt,
      header: 'Total Debt',
      cell: ({ row }) => formatMarketCap(row.original.fundamentals?.total_debt),
    },
    {
      id: 'net_debt',
      accessorFn: (row) => row.fundamentals?.net_debt,
      header: 'Net Debt',
      cell: ({ row }) => formatMarketCap(row.original.fundamentals?.net_debt),
    },
    {
      id: 'insider_pct',
      accessorFn: (row) => row.fundamentals?.insider_pct,
      header: 'Insider %',
      cell: ({ row }) => formatPercent(row.original.fundamentals?.insider_pct),
    },
    {
      id: 'institutional_pct',
      accessorFn: (row) => row.fundamentals?.institutional_pct,
      header: 'Inst %',
      cell: ({ row }) => formatPercent(row.original.fundamentals?.institutional_pct),
    },
    {
      id: 'sector',
      accessorFn: (row) => row.fundamentals?.sector || 'N/A',
      header: 'Sector',
      cell: ({ row }) => row.original.fundamentals?.sector || 'N/A',
      filterFn: (row, columnId, filterValue: string[]) => {
        if (!filterValue || filterValue.length === 0) return true;
        const value = String(row.getValue(columnId) || '');
        return filterValue.includes(value);
      },
    },
    {
      id: 'industry',
      accessorFn: (row) => row.fundamentals?.industry || 'N/A',
      header: 'Industry',
      cell: ({ row }) => (
        <span className="truncate max-w-[150px] block" title={row.original.fundamentals?.industry}>
          {row.original.fundamentals?.industry || 'N/A'}
        </span>
      ),
    },
    {
      id: 'current_price',
      accessorFn: (row) => row.fundamentals?.current_price,
      header: 'Price',
      cell: ({ row }) => {
        const price = row.original.fundamentals?.current_price;
        return price !== 'N/A' ? `$${formatNumber(price)}` : 'N/A';
      },
    },
    {
      id: 'is_etf',
      accessorFn: (row) => (row.is_etf ? 'Yes' : 'No'),
      header: 'ETF',
      cell: ({ row }) => (row.original.is_etf ? 'Yes' : 'No'),
      filterFn: (row, _columnId, filterValue: string) => {
        if (!filterValue) return true;
        if (filterValue === 'yes') return row.original.is_etf;
        if (filterValue === 'no') return !row.original.is_etf;
        return true;
      },
    },
    {
      id: 'thesis',
      accessorFn: (row) => row.thesis || '',
      header: 'Thesis',
      cell: ({ row }) => (
        <ThesisGenerator stock={row.original} onThesisUpdate={onThesisUpdate} />
      ),
    },
    {
      id: 'link',
      accessorFn: (row) => row.stockanalysis_link,
      header: 'Link',
      cell: ({ row }) => (
        <a
          href={row.original.stockanalysis_link}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center w-8 h-8 bg-blue-50 hover:bg-blue-100 rounded-lg transition"
          title="View on StockAnalysis"
        >
          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      ),
      size: 60,
    },
  ];
}
