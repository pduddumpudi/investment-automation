import { PresetFilter } from './PresetFilter';

interface MultiSelectOption {
  label: string;
  value: string;
}

interface MultiSelectProps {
  label: string;
  options: MultiSelectOption[];
  values: string[];
  onChange: (values: string[]) => void;
}

function MultiSelect({ label, options, values, onChange }: MultiSelectProps) {
  const toggleValue = (value: string) => {
    if (values.includes(value)) {
      onChange(values.filter(item => item !== value));
    } else {
      onChange([...values, value]);
    }
  };

  return (
    <details className="relative">
      <summary className="cursor-pointer select-none border rounded-lg px-3 py-2 text-sm bg-white">
        {label}{values.length > 0 ? ` (${values.length})` : ''}
      </summary>
      <div className="absolute z-20 mt-2 w-56 rounded-lg border bg-white shadow-lg p-3 space-y-2">
        {options.map(option => (
          <label key={option.value} className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={values.includes(option.value)}
              onChange={() => toggleValue(option.value)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <span>{option.label}</span>
          </label>
        ))}
        {options.length === 0 && (
          <div className="text-xs text-gray-500">No options</div>
        )}
      </div>
    </details>
  );
}

interface FilterBarProps {
  globalFilter: string;
  setGlobalFilter: (value: string) => void;
  sourceFilter: string[];
  setSourceFilter: (values: string[]) => void;
  activityFilter: string[];
  setActivityFilter: (values: string[]) => void;
  sectorFilter: string[];
  setSectorFilter: (values: string[]) => void;
  isEtfFilter: string;
  setIsEtfFilter: (value: string) => void;
  peFilter: string;
  setPeFilter: (value: string) => void;
  aboveLowFilter: string;
  setAboveLowFilter: (value: string) => void;
  investorCountFilter: string;
  setInvestorCountFilter: (value: string) => void;
  resultCount: number;
  totalCount: number;
  sectorOptions: string[];
  onClearFilters: () => void;
}

export function FilterBar({
  globalFilter,
  setGlobalFilter,
  sourceFilter,
  setSourceFilter,
  activityFilter,
  setActivityFilter,
  sectorFilter,
  setSectorFilter,
  isEtfFilter,
  setIsEtfFilter,
  peFilter,
  setPeFilter,
  aboveLowFilter,
  setAboveLowFilter,
  investorCountFilter,
  setInvestorCountFilter,
  resultCount,
  totalCount,
  sectorOptions,
  onClearFilters,
}: FilterBarProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6 space-y-4">
      <div className="flex flex-wrap gap-4 items-center">
        <div className="flex-1 min-w-[220px]">
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
              value={globalFilter}
              onChange={(e) => setGlobalFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={onClearFilters}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Clear filters
        </button>

        <div className="text-sm text-gray-500">
          Showing <span className="font-semibold text-gray-900">{resultCount}</span> of{' '}
          <span className="font-semibold text-gray-900">{totalCount}</span> stocks
        </div>
      </div>

      <div className="flex flex-wrap gap-4 items-end">
        <MultiSelect
          label="Sources"
          options={[
            { label: 'Dataroma', value: 'Dataroma' },
            { label: 'Substack', value: 'Substack' },
          ]}
          values={sourceFilter}
          onChange={setSourceFilter}
        />

        <MultiSelect
          label="Activity"
          options={[
            { label: 'New', value: 'New' },
            { label: 'Buy', value: 'Buy' },
            { label: 'Add', value: 'Add' },
            { label: 'Sell', value: 'Sell' },
            { label: 'Reduce', value: 'Reduce' },
            { label: 'Hold', value: 'Hold' },
          ]}
          values={activityFilter}
          onChange={setActivityFilter}
        />

        <MultiSelect
          label="Sector"
          options={sectorOptions.map(sector => ({ label: sector, value: sector }))}
          values={sectorFilter}
          onChange={setSectorFilter}
        />

        <label className="flex flex-col gap-1 text-sm">
          <span className="text-gray-500">ETF</span>
          <select
            value={isEtfFilter}
            onChange={(event) => setIsEtfFilter(event.target.value)}
            className="border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          >
            <option value="">All</option>
            <option value="yes">Only ETFs</option>
            <option value="no">Exclude ETFs</option>
          </select>
        </label>

        <PresetFilter
          label="PE Ratio"
          value={peFilter}
          onChange={setPeFilter}
          options={[
            { label: '<10 (Deep Value)', value: 'lt10' },
            { label: '10-15 (Value)', value: '10-15' },
            { label: '15-25 (Fair)', value: '15-25' },
            { label: '25-40 (Growth)', value: '25-40' },
            { label: '>40 (Expensive)', value: 'gt40' },
            { label: 'N/A', value: 'na' },
          ]}
        />

        <PresetFilter
          label="% Above 52W Low"
          value={aboveLowFilter}
          onChange={setAboveLowFilter}
          options={[
            { label: '<5% (Near Low)', value: 'lt5' },
            { label: '5-15%', value: '5-15' },
            { label: '15-30%', value: '15-30' },
            { label: '>30%', value: 'gt30' },
          ]}
        />

        <PresetFilter
          label="Investor Count"
          value={investorCountFilter}
          onChange={setInvestorCountFilter}
          options={[
            { label: '1', value: '1' },
            { label: '2-3', value: '2-3' },
            { label: '4-5', value: '4-5' },
            { label: '6+', value: '6+' },
          ]}
        />
      </div>
    </div>
  );
}
