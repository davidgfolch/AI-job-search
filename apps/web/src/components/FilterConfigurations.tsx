import type { JobListParams } from '../api/jobs';
import { useFilterConfigurations } from '../hooks/useFilterConfigurations';
import { ConfigurationInput } from './configurations/ConfigurationInput';
import { ConfigurationDropdown } from './configurations/ConfigurationDropdown';
import './FilterConfigurations.css';

interface FilterConfigurationsProps {
    currentFilters: JobListParams;
    onLoadConfig: (filters: JobListParams) => void;
    onMessage?: (message: string, type: 'success' | 'error') => void;
}

export default function FilterConfigurations({ currentFilters, onLoadConfig, onMessage }: FilterConfigurationsProps) {
    const {
        configName,
        isOpen,
        highlightIndex,
        wrapperRef,
        filteredConfigs,
        saveConfiguration,
        loadConfiguration,
        deleteConfiguration,
        handleKeyDown,
        handleChange,
        handleFocus,
        handleBlur,
        exportToDefaults,
        setHighlightIndex
    } = useFilterConfigurations({ currentFilters, onLoadConfig, onMessage });

    return (
        <div className="filter-configurations">
            <label htmlFor="filter-config-input">Filter Configurations:</label>
            <div className="config-controls" ref={wrapperRef}>
                <ConfigurationInput
                    configName={configName}
                    onChange={handleChange}
                    onKeyDown={handleKeyDown}
                    onFocus={handleFocus}
                    onClick={handleFocus}
                    onBlur={handleBlur}
                    onSave={saveConfiguration}
                    onExport={exportToDefaults}
                />
                <ConfigurationDropdown
                    isOpen={isOpen}
                    filteredConfigs={filteredConfigs}
                    highlightIndex={highlightIndex}
                    onLoad={loadConfiguration}
                    onDelete={deleteConfiguration}
                    setHighlightIndex={setHighlightIndex}
                />
            </div>
        </div>
    );
}
