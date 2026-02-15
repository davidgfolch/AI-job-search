import { useState } from 'react';
import type { JobListParams } from '../api/ViewerApi';
import { BOOLEAN_FILTERS } from "../constants";
import './Filters.css';
import HistoryInput from "../../common/components/core/HistoryInput";
import FilterConfigurations from './FilterConfigurations';
import SqlEditor from "../../common/components/core/SqlEditor";
import { useFilterExpanded } from '../hooks/useFilterExpanded';

interface BooleanFiltersProps {
    filters: JobListParams;
    onFiltersChange: (filters: Partial<JobListParams>) => void;
    onMessage?: (text: string, type: 'success' | 'error') => void;
    onConfigNameChange?: (name: string) => void;
    refreshJobs?: () => Promise<void>;
    configCount?: number;
    onConfigsLoaded?: (count: number) => void;
}

export default function BooleanFilters({ filters, onFiltersChange, onMessage, onConfigNameChange, refreshJobs, configCount, onConfigsLoaded }: BooleanFiltersProps) {
    const { isExpanded, setIsExpanded } = useFilterExpanded({ configCount });
    const [isSqlEditorOpen, setIsSqlEditorOpen] = useState(false);
    const handleSearchChange = (search: string) => {
        onFiltersChange({ ...filters, search, page: 1 });
    };
    const handlePillClick = (key: keyof JobListParams, value: boolean) => {
        // If clicking the same value, toggle it off (undefined)
        // If clicking different value, set it to that value
        const newValue = filters[key];
        onFiltersChange({ [key]: (newValue === value ? undefined : value) });
    };
    const hasActiveFilters = BOOLEAN_FILTERS.some(filter => filters[filter.key] !== undefined)
        || !!filters.sql_filter || !!filters.days_old || !!filters.salary;
    return (
        <>
            <div className="boolean-filters">
                <div className="boolean-filters-header">
                    <FilterConfigurations
                        currentFilters={filters}
                        onLoadConfig={(loadedFilters, name) => {
                            onFiltersChange({ ...loadedFilters, page: 1 });
                            refreshJobs?.();
                            if (onConfigNameChange && name) {
                                onConfigNameChange(name);
                            }
                        }}
                        onMessage={onMessage}
                        isExpanded={isExpanded}
                        onToggleExpand={() => setIsExpanded(!isExpanded)}
                        hasActiveFilters={hasActiveFilters}
                        onConfigsLoaded={onConfigsLoaded}/>
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
                                    className="compact-input"/>
                            </div>
                            <label className="compact-filter">
                                Days old:
                                <input name="days_old" type="number" value={filters.days_old || ''}
                                    onChange={(e) => onFiltersChange({ days_old: parseInt(e.target.value) || undefined })}
                                    className="compact-input"/>
                            </label>
                            <div className="compact-filter">
                                <label htmlFor="filter-salary">Salary (Regex):</label>
                                <HistoryInput id="filter-salary"
                                    storageKey="history_salary"
                                    type="text"
                                    value={filters.salary || ''}
                                    onValueChange={(val) => onFiltersChange({ salary: val })}
                                    className="compact-input"/>
                            </div>
                            <div className="compact-filter sql-filter">
                                <div style={{ alignItems: 'center', justifyContent: 'normal', gap: '1rem' }}>
                                    <label htmlFor="filter-sql">SQL Where Filter:</label>
                                    <button type="button" 
                                        onClick={() => setIsSqlEditorOpen(true)}
                                        style={{ marginLeft: '1rem' }}
                                        className="btn btn-primary">
                                        SQL Editor
                                    </button>
                                </div>
                                <HistoryInput id="filter-sql"
                                    storageKey="history_sql"
                                    type="text"
                                    value={filters.sql_filter || ''}
                                    onValueChange={(val) => onFiltersChange({ sql_filter: val })}
                                    placeholder="e.g. salary > 50000 AND title LIKE '%Senior%'"
                                    className="sql-input"/>
                            </div>
                            <div className="compact-filter sort-filter">
                                <label htmlFor="sort_field">Sort:</label>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    <select id="sort_field" name="sort_field"
                                        value={filters.order?.split(' ')[0] || 'created'}
                                        onChange={(e) => {
                                            const newField = e.target.value;
                                            const currentDir = filters.order?.split(' ')[1] || 'desc';
                                            onFiltersChange({ order: `${newField} ${currentDir}` });
                                        }}
                                        className="compact-select"
                                        aria-label="Sort Field">
                                        <option value="created">Created</option>
                                        <option value="modified">Modified</option>
                                        <option value="salary">Salary</option>
                                        <option value="cv_match_percentage">Match %</option>
                                    </select>
                                    <select name="sort_dir" value={filters.order?.split(' ')[1] || 'desc'}
                                        onChange={(e) => {
                                            const newDir = e.target.value;
                                            const currentField = filters.order?.split(' ')[0] || 'created';
                                            onFiltersChange({ order: `${currentField} ${newDir}` });
                                        }}
                                        className="compact-select"
                                        aria-label="Sort Direction"
                                        style={{ width: '80px' }}>
                                        <option value="desc">Desc</option>
                                        <option value="asc">Asc</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div className="boolean-filter-groups">
                            <div className="filter-group">
                                <div className="filter-pills-row">
                                    <div className="pills-section">
                                        <span className="section-label">Include:</span>
                                        {BOOLEAN_FILTERS.map((filter) => (
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
                                        {BOOLEAN_FILTERS.map((filter) => (
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
                <SqlEditor isOpen={isSqlEditorOpen}
                    initialValue={filters.sql_filter || ''}
                    onSave={(value) => {
                        onFiltersChange({ sql_filter: value });
                        setIsSqlEditorOpen(false);
                    }}
                    onClose={() => setIsSqlEditorOpen(false)}/>
            </div>
        </>
    );
}
