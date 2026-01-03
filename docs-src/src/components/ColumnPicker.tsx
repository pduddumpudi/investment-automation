import type { ColumnConfig } from '../types/stock';

interface ColumnPickerProps {
  columns: ColumnConfig[];
  onToggle: (id: string) => void;
  onReset: () => void;
  onClose: () => void;
  shareUrl: string;
}

export function ColumnPicker({ columns, onToggle, onReset, onClose, shareUrl }: ColumnPickerProps) {
  const groupedColumns = {
    basic: columns.filter(c => c.group === 'basic'),
    valuation: columns.filter(c => c.group === 'valuation'),
    quality: columns.filter(c => c.group === 'quality'),
    income: columns.filter(c => c.group === 'income'),
    other: columns.filter(c => c.group === 'other'),
  };

  const copyShareUrl = () => {
    navigator.clipboard.writeText(shareUrl);
    alert('Share URL copied to clipboard!');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[80vh] overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Column Settings</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 overflow-y-auto max-h-[50vh]">
          {Object.entries(groupedColumns).map(([group, cols]) => (
            cols.length > 0 && (
              <div key={group} className="mb-4">
                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                  {group.charAt(0).toUpperCase() + group.slice(1)}
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {cols.map(col => (
                    <label
                      key={col.id}
                      className="flex items-center gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={col.visible}
                        onChange={() => onToggle(col.id)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm">{col.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            )
          ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-gray-50 flex justify-between items-center">
          <button
            onClick={onReset}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Reset to Defaults
          </button>
          <div className="flex gap-2">
            <button
              onClick={copyShareUrl}
              className="px-4 py-2 text-sm bg-gray-200 hover:bg-gray-300 rounded-lg transition flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              Share View
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm bg-blue-600 text-white hover:bg-blue-700 rounded-lg transition"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
