interface StatisticsFiltersProps {
    timeRange: string;
    onTimeRangeChange: (value: string) => void;
    includeOldJobs: boolean;
    onIncludeOldJobsChange: (checked: boolean) => void;
    className?: string;
    style?: React.CSSProperties;
}

const TIME_RANGE_OPTIONS = [
    { value: 'All', label: 'All' },
    { value: 'Last year', label: 'Last year' },
    { value: 'Last 6 months', label: 'Last 6 months' },
    { value: 'Last 3 months', label: 'Last 3 months' },
    { value: 'Last month', label: 'Last month' },
    { value: 'Last week', label: 'Last week' },
    { value: 'Last day', label: 'Last day' },
];

const StatisticsFilters: React.FC<StatisticsFiltersProps> = ({
    timeRange, onTimeRangeChange, includeOldJobs, onIncludeOldJobsChange, className, style
}) => (
    <div className={className} style={{ display: 'flex', alignItems: 'center', gap: '16px', ...style }}>
        <label>
            Date Range:
            <select
                value={timeRange}
                onChange={(e) => onTimeRangeChange(e.target.value)}
                style={{ marginLeft: '8px', padding: '5px', borderRadius: '4px', border: '1px solid #ccc' }}
            >
                {TIME_RANGE_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
            </select>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
               title="Include old job's snapshots">
            <input
                type="checkbox"
                checked={includeOldJobs}
                onChange={(e) => onIncludeOldJobsChange(e.target.checked)}
                style={{ marginRight: '8px', cursor: 'pointer' }}
            />
            Include old jobs
        </label>
    </div>
);

export default StatisticsFilters;
