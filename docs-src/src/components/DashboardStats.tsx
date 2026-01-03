import type { Stats } from '../types/stock';

interface DashboardStatsProps {
  stats: Stats;
  total: number;
}

export function DashboardStats({ stats, total }: DashboardStatsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white rounded-lg shadow-sm p-4 border-l-4 border-blue-500">
        <div className="text-3xl font-bold text-blue-600">{total}</div>
        <div className="text-sm text-gray-500">Total Stocks</div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-4 border-l-4 border-green-500">
        <div className="text-3xl font-bold text-green-600">{stats.dataroma_stocks}</div>
        <div className="text-sm text-gray-500">From Dataroma</div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-4 border-l-4 border-purple-500">
        <div className="text-3xl font-bold text-purple-600">{stats.substack_stocks}</div>
        <div className="text-sm text-gray-500">From Substack</div>
      </div>

      <div className="bg-white rounded-lg shadow-sm p-4 border-l-4 border-amber-500">
        <div className="text-3xl font-bold text-amber-600">{stats.both_sources}</div>
        <div className="text-sm text-gray-500">From Both Sources</div>
      </div>
    </div>
  );
}
