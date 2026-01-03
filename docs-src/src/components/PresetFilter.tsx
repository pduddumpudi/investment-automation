interface PresetOption {
  label: string;
  value: string;
}

interface PresetFilterProps {
  label: string;
  value: string;
  options: PresetOption[];
  onChange: (value: string) => void;
}

export function PresetFilter({ label, value, options, onChange }: PresetFilterProps) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-gray-500">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
      >
        <option value="">All</option>
        {options.map(option => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
