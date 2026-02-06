import React from 'react';
import './FilterConfigurations.css';
import type { JobListParams } from '../api/ViewerApi';
import { useFilterConfigurations } from './configurations/hooks/useFilterConfigurations';
import { ConfigurationInput } from './configurations/ConfigurationInput';
import { ConfigurationDropdown } from './configurations/ConfigurationDropdown';
import { PinnedConfigurations } from './configurations/PinnedConfigurations';
import ConfirmModal from '../../common/components/core/ConfirmModal';

const CLEAN_OLD_JOBS_CONFIG = {
    "name": "Clean - Delete old jobs",
    "filters": {
        "page": 1,
        "size": 20,
        "days_old": undefined,
        "search": "",
        "order": "created desc",
        "salary": "",
        "sql_filter": "(DATE(created) < DATE_SUB(CURDATE(), INTERVAL 15 DAY) and applied = 0 and flagged = 0 and seen = 0) OR (DATE(created) < DATE_SUB(CURDATE(), INTERVAL 25 DAY) and applied = 0 and flagged = 0)",
    }
};

interface FilterConfigurationsProps {
    currentFilters: JobListParams;
    onLoadConfig: (filters: JobListParams, name: string) => void;
    onMessage?: (message: string, type: 'success' | 'error') => void;
    isExpanded: boolean;
    onToggleExpand: () => void;
    hasActiveFilters: boolean;
}

const ADDITIONAL_DEFAULTS = [CLEAN_OLD_JOBS_CONFIG];

export default function FilterConfigurations({ currentFilters, onLoadConfig, onMessage, isExpanded, onToggleExpand, hasActiveFilters }: FilterConfigurationsProps) {
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
        setHighlightIndex,
        confirmModal,
        toggleNotification,
        toggleStatistics,
        togglePin,
        isWatching,
        watcherResults,
        lastCheckTime,
        toggleWatch,
        savedConfigs,
        savedConfigName
    } = useFilterConfigurations({ 
        currentFilters, 
        onLoadConfig, 
        onMessage, 
        additionalDefaults: ADDITIONAL_DEFAULTS 
    });

    const pinnedConfigs = savedConfigs.filter(c => c.pinned);

    return (
        <div className="filter-configurations-wrapper">
            <ConfirmModal
                isOpen={confirmModal.isOpen}
                message={confirmModal.message}
                onConfirm={confirmModal.onConfirm}
                onCancel={confirmModal.close}
            />
            <div className="filter-configurations">
                <button className={`toggle-button ${hasActiveFilters ? 'has-active' : ''}`}
                    onClick={onToggleExpand}
                    title={isExpanded ? "Collapse filters" : "Expand filters"}
                >
                    Filters {hasActiveFilters && <span className="color-green">●</span>} {isExpanded ? '▼' : '▶'}
                </button>
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
                        onWatch={toggleWatch}
                        isWatching={isWatching}
                    />
                    <ConfigurationDropdown
                        isOpen={isOpen}
                        filteredConfigs={filteredConfigs}
                        highlightIndex={highlightIndex}
                        onLoad={loadConfiguration}
                        onDelete={deleteConfiguration}
                        setHighlightIndex={setHighlightIndex}
                        onToggleNotify={toggleNotification}
                        onToggleStats={toggleStatistics}
                        onTogglePin={togglePin}
                        results={watcherResults}
                        lastCheckTime={lastCheckTime}
                    />
                </div>
            </div>
            <PinnedConfigurations
                pinnedConfigs={pinnedConfigs}
                onLoad={loadConfiguration}
                onUnpin={togglePin}
                results={watcherResults}
                selectedConfigName={savedConfigName}
            />
        </div>
    );
}
