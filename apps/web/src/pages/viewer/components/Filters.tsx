import { useState } from 'react';
import type { JobListParams } from '../api/ViewerApi';
import { BOOLEAN_FILTERS } from "../constants";
import './Filters.css';
import FilterConfigurations from './FilterConfigurations';
import SqlEditor from "../../common/components/core/SqlEditor";
import { useFilterExpanded } from '../hooks/useFilterExpanded';
import { GeneralFilters, BooleanFilterGroups, ModalityFilter } from './filters/components';

interface BooleanFiltersProps {
    filters: JobListParams;
    onFiltersChange: (filters: Partial<JobListParams>) => void;
    onMessage?: (text: string, type: 'success' | 'error') => void;
    onConfigNameChange?: (name: string) => void;
    refreshJobs?: () => Promise<void>;
    configCount?: number;
    onConfigsLoaded?: (count: number) => void;
    modalityValues?: string[];
}

export default function BooleanFilters({ filters, onFiltersChange, onMessage, onConfigNameChange, refreshJobs, configCount, onConfigsLoaded, modalityValues }: BooleanFiltersProps) {
    const { isExpanded, setIsExpanded } = useFilterExpanded({ configCount });
    const [isSqlEditorOpen, setIsSqlEditorOpen] = useState(false);

    const hasActiveFilters = BOOLEAN_FILTERS.some(filter => filters[filter.key] !== undefined)
        || !!filters.sql_filter || !!filters.days_old || !!filters.salary || (filters.modality && filters.modality.length > 0);
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
                        <GeneralFilters 
                            filters={filters} 
                            onFiltersChange={onFiltersChange} 
                            onOpenSqlEditor={() => setIsSqlEditorOpen(true)} 
                        />
                        <div className="filters-row">
                            <BooleanFilterGroups 
                                filters={filters} 
                                onFiltersChange={onFiltersChange} 
                            />
                            <ModalityFilter 
                                filters={filters} 
                                onFiltersChange={onFiltersChange} 
                                modalityValues={modalityValues} 
                            />
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
