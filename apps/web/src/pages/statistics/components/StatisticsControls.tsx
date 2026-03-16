interface StatisticsControlsProps {
    timeRange: string;
    setTimeRange: (value: string) => void;
    includeOldJobs: boolean;
    setIncludeOldJobs: (value: boolean) => void;
    columns: number;
    setColumns: (value: number) => void;
}

const StatisticsControls: React.FC<StatisticsControlsProps> = ({
    timeRange, setTimeRange, includeOldJobs, setIncludeOldJobs, columns, setColumns
}) => (
    <div className="statistics-controls">
        <div className="layout-controls">
            <span className="layout-label">Date Range:</span>
            <select 
                className="date-range-select"
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                style={{ marginRight: '20px', padding: '5px', borderRadius: '4px', border: '1px solid #ccc' }}
            >
                <option value="All">All</option>
                <option value="Last year">Last year</option>
                <option value="Last 6 months">Last 6 months</option>
                <option value="Last 3 months">Last 3 months</option>
                <option value="Last month">Last month</option>
                <option value="Last week">Last week</option>
                <option value="Last day">Last day</option>
            </select>

            <label style={{ marginRight: '20px', display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                   title="Include old job's snapshots">
                <input
                    type="checkbox"
                    checked={includeOldJobs}
                    onChange={(e) => setIncludeOldJobs(e.target.checked)}
                    style={{ marginRight: '8px', cursor: 'pointer' }}
                />
                Include old jobs
            </label>

            <span className="layout-label">Layout:</span>
            <div className="layout-buttons">
                <button 
                    className={`layout-btn ${columns === 1 ? 'active' : ''}`}
                    onClick={() => setColumns(1)}
                    title="Single Column"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    </svg>
                </button>
                <button 
                    className={`layout-btn ${columns === 2 ? 'active' : ''}`}
                    onClick={() => setColumns(2)}
                    title="Two Columns"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="12" y1="3" x2="12" y2="21"></line>
                    </svg>
                </button>
                <button 
                    className={`layout-btn ${columns === 3 ? 'active' : ''}`}
                    onClick={() => setColumns(3)}
                    title="Three Columns"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="9" y1="3" x2="9" y2="21"></line>
                        <line x1="15" y1="3" x2="15" y2="21"></line>
                    </svg>
                </button>
            </div>
        </div>
    </div>
);

export default StatisticsControls;