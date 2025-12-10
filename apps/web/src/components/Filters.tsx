import { useState } from 'react';
import type { JobListParams } from '../api/jobs';
import './Filters.css';
import HistoryInput from './HistoryInput';
import FilterConfigurations from './FilterConfigurations';

interface BooleanFiltersProps {
    filters: JobListParams;
    onFiltersChange: (filters: Partial<JobListParams>) => void;
    onMessage?: (text: string, type: 'success' | 'error') => void;
}

interface FilterItem {
    key: keyof JobListParams;
    label: string;
}

// Flattened list of all boolean filters
const ALL_FILTERS: FilterItem[] = [
    // Status Flags
    { key: 'flagged', label: 'Flagged' },
    { key: 'like', label: 'Like' },
    { key: 'ignored', label: 'Ignored' },
    { key: 'seen', label: 'Seen' },
    // Application Status
    { key: 'applied', label: 'Applied' },
    { key: 'discarded', label: 'Discarded' },
    { key: 'closed', label: 'Closed' },
    // Interview Process
    { key: 'interview_rh', label: 'Interview (RH)' },
    { key: 'interview', label: 'Interview' },
    { key: 'interview_tech', label: 'Interview (Tech)' },
    { key: 'interview_technical_test', label: 'Technical Test' },
    { key: 'interview_technical_test_done', label: 'Technical Test Done' },
    // Other
    { key: 'ai_enriched', label: 'AI Enriched' },
    { key: 'easy_apply', label: 'Easy Apply' },
];

export default function BooleanFilters({ filters, onFiltersChange, onMessage }: BooleanFiltersProps) {
    const [isExpanded, setIsExpanded] = useState(true);

    const handleSearchChange = (search: string) => {
        onFiltersChange({ ...filters, search, page: 1 });
    };

    const handlePillClick = (key: keyof JobListParams, value: boolean) => {
        // If clicking the same value, toggle it off (undefined)
        // If clicking different value, set it to that value
        const newValue = filters[key];
        onFiltersChange({ [key]: (newValue === value ? undefined : value) });
    };

    const hasActiveFilters = ALL_FILTERS.some(filter => filters[filter.key] !== undefined)
        || !!filters.sql_filter || !!filters.days_old || !!filters.salary;

    return (
        <>
            <div className="boolean-filters">
                <div className="boolean-filters-header">
                    <FilterConfigurations
                        currentFilters={filters}
                        onLoadConfig={(loadedFilters) => onFiltersChange({ ...loadedFilters, page: 1 })}
                        onMessage={onMessage}
                    />
                    <button className={`toggle-button ${hasActiveFilters ? 'has-active' : ''}`}
                        onClick={() => setIsExpanded(!isExpanded)}>
                        Filters {hasActiveFilters && <span className="color-green">●</span>} {isExpanded ? '▼' : '▶'}
                    </button>
                </div>

                {isExpanded && (
                    <div className="filters-content">
                        <div className="general-filters">
                            <div className="compact-filter">
                                <label htmlFor="filter-search">Search:</label>
                                <HistoryInput
                                    id="filter-search"
                                    storageKey="history_search"
                                    type="text"
                                    placeholder="Search jobs..."
                                    value={filters.search || ''}
                                    onValueChange={handleSearchChange}
                                    className="compact-input"
                                />
                            </div>

                            <label className="compact-filter">
                                Days old:
                                <input type="number" value={filters.days_old || ''}
                                    onChange={(e) => onFiltersChange({ days_old: parseInt(e.target.value) || undefined })}
                                    className="compact-input" />
                            </label>
                            <div className="compact-filter">
                                <label htmlFor="filter-salary">Salary (Regex):</label>
                                <HistoryInput
                                    id="filter-salary"
                                    storageKey="history_salary"
                                    type="text"
                                    value={filters.salary || ''}
                                    onValueChange={(val) => onFiltersChange({ salary: val })}
                                    className="compact-input"
                                />
                            </div>
                            <div className="compact-filter sql-filter">
                                <label htmlFor="filter-sql">SQL Where Filter:</label>
                                <HistoryInput
                                    id="filter-sql"
                                    storageKey="history_sql"
                                    type="text"
                                    value={filters.sql_filter || ''}
                                    onValueChange={(val) => onFiltersChange({ sql_filter: val })}
                                    placeholder="e.g. salary > 50000 AND title LIKE '%Senior%'"
                                    className="sql-input"
                                />
                            </div>
                            <label className="compact-filter">
                                Sort:
                                <select value={filters.order || 'created desc'}
                                    onChange={(e) => onFiltersChange({ order: e.target.value })}
                                    className="compact-select">
                                    <option value="created desc">Created (Newest)</option>
                                    <option value="created asc">Created (Oldest)</option>
                                    <option value="salary desc">Salary (High-Low)</option>
                                    <option value="salary asc">Salary (Low-High)</option>
                                    <option value="cv_match_percentage desc">Match % (High-Low)</option>
                                </select>
                            </label>
                        </div>

                        <div className="boolean-filter-groups">
                            <div className="filter-group">
                                <div className="filter-pills-row">
                                    <div className="pills-section">
                                        <span className="section-label">Include:</span>
                                        {ALL_FILTERS.map((filter) => (
                                            <button key={`${filter.key}-true`}
                                                className={`filter-pill ${filters[filter.key] === true ? 'active-true' : ''}`}
                                                onClick={() => handlePillClick(filter.key, true)}>
                                                {filter.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                            <div className="filter-group">
                                <div className="filter-pills-row">
                                    <div className="pills-section">
                                        <span className="section-label">Exclude:</span>
                                        {ALL_FILTERS.map((filter) => (
                                            <button key={`${filter.key}-false`}
                                                className={`filter-pill ${filters[filter.key] === false ? 'active-false' : ''}`}
                                                onClick={() => handlePillClick(filter.key, false)}>
                                                {filter.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
}
