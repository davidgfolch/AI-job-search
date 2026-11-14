import type { JobListParams } from '../../api/ViewerApi';

interface BehaviourFiltersProps {
    filters: JobListParams;
    onFiltersChange: (filters: Partial<JobListParams>) => void;
    onExpandChange: (expanded: boolean) => void;
}

export function BehaviourFilters({ filters, onFiltersChange, onExpandChange }: BehaviourFiltersProps) {
    const handleFilterExpandedClick = () => {
        const next = filters.filter_expanded === true ? null : true;
        onFiltersChange({ filter_expanded: next });
        onExpandChange(next === true);
    };
    return (
        <div className="filter-group behaviour-filters-group">
            <div className="filter-pills-row">
                <div className="pills-section">
                    <button
                        className={`filter-pill ${filters.auto_select_all === true ? 'active-true' : ''}`}
                        title="Auto select all jobs in the filter, including pages that are not loaded"
                        onClick={() => onFiltersChange({ auto_select_all: filters.auto_select_all === true ? null : true })}>
                        Auto select all
                    </button>
                    <button
                        className={`filter-pill ${filters.filter_expanded === true ? 'active-true' : ''}`}
                        title="Expand the filters panel when this configuration is loaded"
                        onClick={handleFilterExpandedClick}>
                        Filter expanded
                    </button>
                </div>
            </div>
        </div>
    );
}
