import { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  getExpandedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type ExpandedState,
} from '@tanstack/react-table';
import type { Stock, ColumnConfig } from '../types/stock';
import { ExpandedRow } from './ExpandedRow';

interface StockTableProps {
  stocks: Stock[];
  visibleColumns: ColumnConfig[];
}

// Helper to format numbers
function formatNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === 'N/A') return 'N/A';
  if (typeof value === 'string') return value;
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

// Helper to format market cap
function formatMarketCap(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === 'N/A') return 'N/A';
  if (typeof value === 'string') return value;
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
}

// Helper to get PE color class
function getPEColorClass(pe: number | string): string {
  if (typeof pe !== 'number') return '';
  if (pe < 0) return 'text-gray-400';
  if (pe < 15) return 'text-green-600 font-semibold';
  if (pe < 25) return 'text-yellow-600';
  return 'text-red-600';
}

// Helper to get activity badge class
function getActivityBadgeClass(activity: string): string {
  const action = activity.toLowerCase();
  if (action === 'new' || action === 'buy') return 'bg-green-100 text-green-800';
  if (action === 'add') return 'bg-blue-100 text-blue-800';
  if (action === 'sell') return 'bg-red-100 text-red-800';
  if (action === 'reduce') return 'bg-orange-100 text-orange-800';
  return 'bg-gray-100 text-gray-600';
}

export function StockTable({ stocks, visibleColumns }: StockTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [expanded, setExpanded] = useState<ExpandedState>({});

  const visibleColumnIds = useMemo(() => new Set(visibleColumns.map(c => c.id)), [visibleColumns]);

  const columns = useMemo<ColumnDef<Stock>[]>(() => {
    const allColumns: ColumnDef<Stock>[] = [
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
      },
      {
        id: 'pb_ratio',
        accessorFn: (row) => row.fundamentals?.pb_ratio,
        header: 'PB Ratio',
        cell: ({ row }) => formatNumber(row.original.fundamentals?.pb_ratio),
      },
      {
        id: 'week_52_range',
        header: '52W Range',
        cell: ({ row }) => {
          const high = row.original.fundamentals?.week_52_high;
          const low = row.original.fundamentals?.week_52_low;
          if (high === 'N/A' || low === 'N/A') return 'N/A';
          return `$${formatNumber(low)} - $${formatNumber(high)}`;
        },
      },
      {
        id: 'sources',
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
      },
      {
        id: 'investors',
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
        id: 'insider_pct',
        accessorFn: (row) => row.fundamentals?.insider_pct,
        header: 'Insider %',
        cell: ({ row }) => {
          const pct = row.original.fundamentals?.insider_pct;
          return pct !== 'N/A' ? `${formatNumber(pct)}%` : 'N/A';
        },
      },
      {
        id: 'institutional_pct',
        accessorFn: (row) => row.fundamentals?.institutional_pct,
        header: 'Inst %',
        cell: ({ row }) => {
          const pct = row.original.fundamentals?.institutional_pct;
          return pct !== 'N/A' ? `${formatNumber(pct)}%` : 'N/A';
        },
      },
      {
        id: 'sector',
        accessorFn: (row) => row.fundamentals?.sector,
        header: 'Sector',
        cell: ({ row }) => row.original.fundamentals?.sector || 'N/A',
      },
      {
        id: 'industry',
        accessorFn: (row) => row.fundamentals?.industry,
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
        id: 'thesis',
        header: 'Thesis',
        cell: ({ row }) => {
          const mentions = row.original.substack_data.mentions;
          if (mentions.length === 0) return '-';
          const thesis = mentions[0]?.thesis || '';
          return (
            <span className="truncate max-w-[200px] block text-sm text-gray-600" title={thesis}>
              {thesis.slice(0, 100)}...
            </span>
          );
        },
      },
      {
        id: 'link',
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

    // Filter to only visible columns, but always include expander and link
    return allColumns.filter(col => {
      if (col.id === 'expander') return true;
      return visibleColumnIds.has(col.id as string);
    });
  }, [visibleColumnIds]);

  const table = useReactTable({
    data: stocks,
    columns,
    state: {
      sorting,
      expanded,
    },
    onSortingChange: setSorting,
    onExpandedChange: setExpanded,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getExpandedRowModel: getExpandedRowModel(),
    getRowCanExpand: () => true,
    initialState: {
      pagination: {
        pageSize: 50,
      },
    },
  });

  return (
    <div>
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            {table.getHeaderGroups().map(headerGroup => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map(header => (
                  <th
                    key={header.id}
                    className={header.column.getCanSort() ? 'cursor-pointer select-none' : ''}
                    onClick={header.column.getToggleSortingHandler()}
                    style={{ width: header.getSize() }}
                  >
                    <div className="flex items-center gap-1">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getCanSort() && (
                        <span className="text-gray-400">
                          {{
                            asc: ' ↑',
                            desc: ' ↓',
                          }[header.column.getIsSorted() as string] ?? ''}
                        </span>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map(row => (
              <>
                <tr key={row.id} className="stock-row hover:bg-blue-50 transition-colors">
                  {row.getVisibleCells().map(cell => (
                    <td key={cell.id}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
                {row.getIsExpanded() && (
                  <tr key={`${row.id}-expanded`}>
                    <td colSpan={row.getVisibleCells().length} className="bg-gray-50 p-0">
                      <ExpandedRow stock={row.original} />
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 border-t bg-gray-50">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Rows per page:</span>
          <select
            value={table.getState().pagination.pageSize}
            onChange={e => table.setPageSize(Number(e.target.value))}
            className="border rounded px-2 py-1 text-sm"
          >
            {[25, 50, 100, 200].map(pageSize => (
              <option key={pageSize} value={pageSize}>
                {pageSize}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => table.setPageIndex(0)}
              disabled={!table.getCanPreviousPage()}
              className="px-2 py-1 border rounded disabled:opacity-50 hover:bg-gray-100"
            >
              {'<<'}
            </button>
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="px-2 py-1 border rounded disabled:opacity-50 hover:bg-gray-100"
            >
              {'<'}
            </button>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="px-2 py-1 border rounded disabled:opacity-50 hover:bg-gray-100"
            >
              {'>'}
            </button>
            <button
              onClick={() => table.setPageIndex(table.getPageCount() - 1)}
              disabled={!table.getCanNextPage()}
              className="px-2 py-1 border rounded disabled:opacity-50 hover:bg-gray-100"
            >
              {'>>'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
