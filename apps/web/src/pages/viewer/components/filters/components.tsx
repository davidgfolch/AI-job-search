import type { JobListParams } from '../../api/ViewerApi';
import { BOOLEAN_FILTERS } from "../../constants";
import HistoryInput from "../../../common/components/core/HistoryInput";
import { FormField } from "../../../common/components/core/FormField";

interface GeneralFiltersProps {
    filters: JobListParams;
    onFiltersChange: (filters: Partial<JobListParams>) => void;
    onOpenSqlEditor: () => void;
}

export function GeneralFilters({ filters, onFiltersChange, onOpenSqlEditor }: GeneralFiltersProps) {
    const handleSearchChange = (search: string) => {
        onFiltersChange({ ...filters, search, page: 1 });
    };

    return (
        <div className="general-filters">
            <FormField id="filter-search" label="Search:" className="compact-filter">
                <HistoryInput
                    id="filter-search"
                    name="filter-search"
                    storageKey="history_search"
                    type="text"
                    placeholder="Search jobs..."
                    value={filters.search || ''}
                    onValueChange={handleSearchChange}
                    className="compact-input"/>
            </FormField>
            <FormField id="days_old" label="Days old:" className="compact-filter">
                <input id="days_old" name="days_old" type="number" value={filters.days_old || ''}
                    onChange={(e) => onFiltersChange({ days_old: parseInt(e.target.value) || undefined })}
                    className="compact-input"/>
            </FormField>
            <FormField id="filter-salary" label="Salary (Regex):" className="compact-filter">
                <HistoryInput id="filter-salary" name="filter-salary"
                    storageKey="history_salary"
                    type="text"
                    value={filters.salary || ''}
                    onValueChange={(val) => onFiltersChange({ salary: val })}
                    className="compact-input"/>
            </FormField>
            <FormField id="filter-sql"
                label={
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'normal', gap: '1rem' }}>
                        <span>SQL Where Filter:</span>
                        <button onClick={onOpenSqlEditor} className="btn-secondary">
                            SQL Editor
                        </button>
                    </div>
                }
                className="compact-filter sql-filter">
                <HistoryInput id="filter-sql" name="filter-sql"
                    storageKey="history_sql"
                    type="text"
                    value={filters.sql_filter || ''}
                    onValueChange={(val) => onFiltersChange({ sql_filter: val })}
                    placeholder="e.g. salary > 50000 AND title LIKE '%Senior%'"
                    className="sql-input"/>
            </FormField>
            <FormField id="sort_field" label="Sort:" className="compact-filter sort-filter">
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
                    <select id="sort_dir" name="sort_dir" value={filters.order?.split(' ')[1] || 'desc'}
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
            </FormField>
        </div>
    );
}

interface BooleanFilterGroupsProps {
    filters: JobListParams;
    onFiltersChange: (filters: Partial<JobListParams>) => void;
}

export function BooleanFilterGroups({ filters, onFiltersChange }: BooleanFilterGroupsProps) {
    const handlePillClick = (key: keyof JobListParams, value: boolean) => {
        const newValue = filters[key];
        onFiltersChange({ [key]: (newValue === value ? undefined : value) });
    };

    return (
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
    );
}

interface ModalityFilterProps {
    filters: JobListParams;
    onFiltersChange: (filters: Partial<JobListParams>) => void;
    modalityValues?: string[];
}

export function ModalityFilter({ filters, onFiltersChange, modalityValues }: ModalityFilterProps) {
    const handleModalityChange = (value: string) => {
        const current = filters.modality || [];
        const newModality = current.includes(value) ? current.filter(v => v !== value) : [...current, value];
        onFiltersChange({ modality: newModality.length > 0 ? newModality : undefined });
    };

    if (!modalityValues || modalityValues.length === 0) return null;

    return (
        <div className="filter-group modality-filter-group">
            <div className="filter-pills-row">
                <div className="pills-section">
                    <span className="section-label">Modality:</span>
                    <button
                        className={`filter-pill ${!filters.modality || filters.modality.length === 0 ? 'active-true' : ''}`}
                        onClick={() => onFiltersChange({ modality: undefined })}>
                        All
                    </button>
                    <button
                        className={`filter-pill ${filters.modality?.includes('NULL') ? 'active-true' : ''}`}
                        onClick={() => handleModalityChange('NULL')}>
                        Not set
                    </button>
                    {modalityValues.map((value) => (
                        <button
                            key={value}
                            className={`filter-pill ${filters.modality?.includes(value) ? 'active-true' : ''}`}
                            onClick={() => handleModalityChange(value)}>
                            {value}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
