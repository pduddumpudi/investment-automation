import { useStockData } from './hooks/useStockData';
import { useColumnPreferences } from './hooks/useColumnPreferences';
import { DashboardStats } from './components/DashboardStats';
import { StockTable } from './components/StockTable';
import { ColumnPicker } from './components/ColumnPicker';
import { FilterBar } from './components/FilterBar';
import { useState } from 'react';

function App() {
  const { data, loading, error } = useStockData();
  const columnPrefs = useColumnPreferences();
  const [showColumnPicker, setShowColumnPicker] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<'all' | 'dataroma' | 'substack' | 'both'>('all');
  const [activityFilter, setActivityFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading investment data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center text-red-600">
          <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h2 className="text-xl font-semibold mb-2">Failed to Load Data</h2>
          <p>{error}</p>
          <p className="mt-2 text-sm text-gray-500">Make sure data/stocks.json exists</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  // Filter stocks based on current filters
  const filteredStocks = data.stocks.filter(stock => {
    // Source filter
    if (sourceFilter === 'dataroma' && !stock.sources.includes('Dataroma')) return false;
    if (sourceFilter === 'substack' && !stock.sources.includes('Substack')) return false;
    if (sourceFilter === 'both' && !(stock.sources.includes('Dataroma') && stock.sources.includes('Substack'))) return false;

    // Activity filter
    if (activityFilter !== 'all' && stock.aggregate_activity.toLowerCase() !== activityFilter.toLowerCase()) return false;

    // Search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesTicker = stock.ticker.toLowerCase().includes(query);
      const matchesCompany = stock.company_name.toLowerCase().includes(query);
      const matchesInvestor = stock.dataroma_data.investors.some(inv =>
        inv.name.toLowerCase().includes(query)
      );
      if (!matchesTicker && !matchesCompany && !matchesInvestor) return false;
    }

    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-full mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                Investment Ideas Dashboard
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Last Updated: {new Date(data.last_updated).toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => setShowColumnPicker(!showColumnPicker)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Columns
            </button>
          </div>
        </div>
      </header>

      {/* Column Picker Modal */}
      {showColumnPicker && (
        <ColumnPicker
          columns={columnPrefs.columns}
          onToggle={columnPrefs.toggleColumn}
          onReset={columnPrefs.resetToDefaults}
          onClose={() => setShowColumnPicker(false)}
          shareUrl={columnPrefs.getShareableUrl()}
        />
      )}

      {/* Main Content */}
      <main className="max-w-full mx-auto px-4 py-6">
        {/* Stats */}
        <DashboardStats stats={data.stats} total={data.total_stocks} />

        {/* Filters */}
        <FilterBar
          sourceFilter={sourceFilter}
          setSourceFilter={setSourceFilter}
          activityFilter={activityFilter}
          setActivityFilter={setActivityFilter}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          resultCount={filteredStocks.length}
          totalCount={data.total_stocks}
        />

        {/* Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <StockTable
            stocks={filteredStocks}
            visibleColumns={columnPrefs.visibleColumns}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t py-4 mt-8">
        <div className="max-w-full mx-auto px-4 text-center text-sm text-gray-500">
          Data sourced from Dataroma.com and Substack newsletters.
          Fundamentals from Yahoo Finance.
        </div>
      </footer>
    </div>
  );
}

export default App;
