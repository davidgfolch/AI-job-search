import { useState } from 'react';
import type { JobListParams } from '../api/jobs';
import './Filters.css';

interface BooleanFiltersProps {
    filters: JobListParams;
    onFiltersChange: (filters: Partial<JobListParams>) => void;
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

export default function BooleanFilters({ filters, onFiltersChange }: BooleanFiltersProps) {
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
        <div className="boolean-filters">
            <button className={`toggle-button ${hasActiveFilters ? 'has-active' : ''}`}
                onClick={() => setIsExpanded(!isExpanded)}>
                Filters {hasActiveFilters && <span className="color-green">●</span>} {isExpanded ? '▼' : '▶'}
            </button>

            {isExpanded && (
                <div className="filters-content">
                    <div className="general-filters">
                        <label className="compact-filter">
                            Search:
                            <input type="text" placeholder="Search jobs..." value={filters.search}
                                onChange={(e) => handleSearchChange(e.target.value)} className="compact-input" />
                        </label>

                        <label className="compact-filter">
                            Days old:
                            <input type="number" value={filters.days_old || ''}
                                onChange={(e) => onFiltersChange({ days_old: parseInt(e.target.value) || undefined })}
                                className="compact-input" />
                        </label>
                        <label className="compact-filter">
                            Salary (Regex):
                            <input type="text" value={filters.salary || ''}
                                onChange={(e) => onFiltersChange({ salary: e.target.value })}
                                className="compact-input" />
                        </label>
                        <label className="compact-filter sql-filter">
                            SQL Where Filter:
                            <input type="text" value={filters.sql_filter || ''}
                                onChange={(e) => onFiltersChange({ sql_filter: e.target.value })}
                                placeholder="e.g. salary > 50000 AND title LIKE '%Senior%'"
                                className="sql-input" />
                        </label>
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
    );
}
