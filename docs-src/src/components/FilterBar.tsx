interface FilterBarProps {
  sourceFilter: 'all' | 'dataroma' | 'substack' | 'both';
  setSourceFilter: (filter: 'all' | 'dataroma' | 'substack' | 'both') => void;
  activityFilter: string;
  setActivityFilter: (filter: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  resultCount: number;
  totalCount: number;
}

export function FilterBar({
  sourceFilter,
  setSourceFilter,
  activityFilter,
  setActivityFilter,
  searchQuery,
  setSearchQuery,
  resultCount,
  totalCount,
}: FilterBarProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="flex flex-wrap gap-4 items-center">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Search ticker, company, or investor..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>
        </div>

        {/* Source Filter */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Source:</span>
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value as typeof sourceFilter)}
            className="border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          >
            <option value="all">All Sources</option>
            <option value="dataroma">Dataroma Only</option>
            <option value="substack">Substack Only</option>
            <option value="both">Both Sources</option>
          </select>
        </div>

        {/* Activity Filter */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Activity:</span>
          <select
            value={activityFilter}
            onChange={(e) => setActivityFilter(e.target.value)}
            className="border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          >
            <option value="all">All Activity</option>
            <option value="new">New Position</option>
            <option value="buy">Buy</option>
            <option value="add">Add</option>
            <option value="sell">Sell</option>
            <option value="reduce">Reduce</option>
            <option value="hold">Hold</option>
          </select>
        </div>

        {/* Result Count */}
        <div className="text-sm text-gray-500">
          Showing <span className="font-semibold text-gray-900">{resultCount}</span> of{' '}
          <span className="font-semibold text-gray-900">{totalCount}</span> stocks
        </div>
      </div>
    </div>
  );
}
