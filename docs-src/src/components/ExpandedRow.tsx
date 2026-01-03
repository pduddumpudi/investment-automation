import type { Stock, Investor, SubstackMention } from '../types/stock';

interface ExpandedRowProps {
  stock: Stock;
}

// Helper to get activity badge class
function getActivityBadgeClass(action: string): string {
  const act = action.toLowerCase();
  if (act === 'new' || act === 'buy') return 'bg-green-100 text-green-800';
  if (act === 'add') return 'bg-blue-100 text-blue-800';
  if (act === 'sell') return 'bg-red-100 text-red-800';
  if (act === 'reduce') return 'bg-orange-100 text-orange-800';
  return 'bg-gray-100 text-gray-600';
}

// Format number helper
function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

// Investor table component
function InvestorTable({ investors }: { investors: Investor[] }) {
  if (investors.length === 0) return null;

  return (
    <div className="mb-4">
      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        Superinvestors ({investors.length})
      </h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-3 py-2 text-left font-medium text-gray-600">Investor</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Portfolio %</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Shares</th>
              <th className="px-3 py-2 text-center font-medium text-gray-600">Activity</th>
              <th className="px-3 py-2 text-center font-medium text-gray-600">Link</th>
            </tr>
          </thead>
          <tbody>
            {investors.map((investor, idx) => (
              <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-3 py-2 font-medium">{investor.name}</td>
                <td className="px-3 py-2 text-right">
                  {investor.portfolio_pct !== null ? `${formatNumber(investor.portfolio_pct)}%` : '-'}
                </td>
                <td className="px-3 py-2 text-right">
                  {investor.shares !== null ? formatNumber(investor.shares) : '-'}
                </td>
                <td className="px-3 py-2 text-center">
                  {investor.activity.action !== 'Hold' ? (
                    <span className={`px-2 py-1 text-xs rounded-full ${getActivityBadgeClass(investor.activity.action)}`}>
                      {investor.activity.action}
                      {investor.activity.percentage !== null && ` ${investor.activity.percentage}%`}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="px-3 py-2 text-center">
                  <a
                    href={investor.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                    title="View investor's portfolio"
                  >
                    <svg className="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Substack mentions component
function SubstackMentions({ mentions }: { mentions: SubstackMention[] }) {
  if (mentions.length === 0) return null;

  return (
    <div>
      <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
        <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
        </svg>
        Mentioned In ({mentions.length})
      </h4>
      <div className="space-y-2">
        {mentions.map((mention, idx) => (
          <div key={idx} className="flex items-start gap-3 p-2 bg-white rounded border">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="font-medium text-purple-700">{mention.publication}</span>
                <a
                  href={mention.article_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
                >
                  Read Article
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
              {mention.thesis && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">{mention.thesis}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function ExpandedRow({ stock }: ExpandedRowProps) {
  const hasInvestors = stock.dataroma_data.investors.length > 0;
  const hasMentions = stock.substack_data.mentions.length > 0;
  const hasThesis = Boolean(stock.thesis && stock.thesis.trim().length > 0);

  if (!hasInvestors && !hasMentions && !hasThesis) {
    return (
      <div className="p-4 text-sm text-gray-500 italic">
        No additional details available for this stock.
      </div>
    );
  }

  return (
    <div className="p-4 expanded-content">
      {hasThesis && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
            <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-7 7-7-7" />
            </svg>
            Thesis
          </h4>
          <div className="text-sm text-gray-700 bg-white border rounded p-3">
            {stock.thesis}
          </div>
        </div>
      )}
      {/* Combined view when stock has both sources */}
      {hasInvestors && hasMentions && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <InvestorTable investors={stock.dataroma_data.investors} />
          <SubstackMentions mentions={stock.substack_data.mentions} />
        </div>
      )}

      {/* Only investors */}
      {hasInvestors && !hasMentions && (
        <InvestorTable investors={stock.dataroma_data.investors} />
      )}

      {/* Only mentions (minimal view per spec) */}
      {!hasInvestors && hasMentions && (
        <div className="flex flex-wrap gap-2">
          {stock.substack_data.mentions.map((mention, idx) => (
            <a
              key={idx}
              href={mention.article_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-3 py-2 bg-purple-50 hover:bg-purple-100 rounded-lg text-sm transition"
            >
              <span className="font-medium text-purple-700">{mention.publication}</span>
              <svg className="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
