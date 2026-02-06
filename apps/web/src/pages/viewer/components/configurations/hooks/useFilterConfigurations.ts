import { useState, useEffect, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import type { JobListParams } from '../../../api/ViewerApi';
import defaultFilterConfigurations from '../../../../../resources/defaultFilterConfigurations.json';
import { FilterConfigService } from '../../../hooks/FilterConfigService';
import { useFilterDropdown } from './useFilterDropdown';
import { useConfirmationModal } from './useConfirmationModal';
import { useConfigDropdownState } from './useConfigDropdownState';
import { useConfigOperations } from './useConfigOperations';
import { useFilterWatcher, type WatcherResult } from './useFilterWatcher';
import { useConfigToggles } from './useConfigToggles';

export interface FilterConfig {
    id?: number;
    name: string;
    filters: JobListParams;
    notify?: boolean;
    statistics?: boolean;
    pinned?: boolean;
}

interface UseFilterConfigurationsProps {
    currentFilters: JobListParams;
    onLoadConfig: (filters: JobListParams, name: string) => void;
    onMessage?: (message: string, type: 'success' | 'error') => void;
    additionalDefaults?: FilterConfig[];
}

export function useFilterConfigurations({
    currentFilters,
    onLoadConfig,
    onMessage,
    additionalDefaults = []
}: UseFilterConfigurationsProps) {
    const service = useMemo(() => new FilterConfigService(), []);
    const [savedConfigs, setSavedConfigs] = useState<FilterConfig[]>([]);
    const [savedConfigName, setSavedConfigName] = useState('');
    const confirmModal = useConfirmationModal();

    const dropdownState = useConfigDropdownState(savedConfigName);
    const { configName, isOpen, setIsOpen, handleChange, handleFocus, handleBlur } = dropdownState;

    const notify = useCallback(
        (msg: string, type: 'success' | 'error') => {
            if (onMessage) onMessage(msg, type);
            else console.warn(`Message (${type}): ${msg}`);
        },
        [onMessage]
    );

    const allDefaults = useMemo(() => 
        [...(defaultFilterConfigurations as any[]), ...additionalDefaults],
        [additionalDefaults]
    );

    const { data: loadedConfigs, error: loadError } = useQuery({
        queryKey: ['filterConfigs', allDefaults.length], // Include defaults length as dependency if needed, or just service
        queryFn: () => service.load(allDefaults),
        staleTime: 1000 * 60 * 5, // 5 minutes
        retry: 1,
    });

    useEffect(() => {
        if (loadedConfigs) {
            setSavedConfigs(loadedConfigs);
        }
    }, [loadedConfigs]);

    useEffect(() => {
        if (loadError) {
             console.error('Failed to load configurations', loadError);
             notify('Failed to load configurations', 'error');
        }
    }, [loadError, notify]);

    const {
        isWatching,
        results: watcherResults,
        lastCheckTime,
        startWatching,
        stopWatching,
        resetWatcher
    } = useFilterWatcher({ savedConfigs });

    const toggleWatch = useCallback(() => {
        if (isWatching) {
            stopWatching();
        } else {
            startWatching();
        }
    }, [isWatching, startWatching, stopWatching]);

    const operations = useConfigOperations({
        service,
        savedConfigs,
        setSavedConfigs,
        currentFilters,
        configName,
        setConfigName: dropdownState.setConfigName,
        setIsOpen,
        setSavedConfigName,
        onLoadConfig,
        notify,
        confirmModal,
    });

    // Intercept loadConfiguration to reset watcher
    // Intercept loadConfiguration to reset watcher
    const handleLoadConfiguration = useCallback((config: FilterConfig) => {
        operations.loadConfiguration(config);
        if (isWatching) {
            resetWatcher(config.name);
        }
    }, [operations.loadConfiguration, isWatching, resetWatcher]);

    const {
        toggleNotification,
        toggleStatistics,
        togglePin
    } = useConfigToggles({
        savedConfigs,
        setSavedConfigs,
        service,
        notify
    });

    const dropdown = useFilterDropdown({
        configs: savedConfigs,
        configName,
        onLoad: handleLoadConfiguration,
        onSave: operations.saveConfiguration,
        onDelete: operations.deleteConfiguration,
        setIsOpen,
        isOpen,
        results: watcherResults,
    });

    useEffect(() => {
        if (!isOpen) dropdown.setHighlightIndex(-1);
    }, [isOpen, dropdown.setHighlightIndex]);

    return {
        configName,
        isOpen,
        highlightIndex: dropdown.highlightIndex,
        wrapperRef: dropdown.wrapperRef,
        filteredConfigs: dropdown.filteredConfigs,
        saveConfiguration: operations.saveConfiguration,
        loadConfiguration: handleLoadConfiguration,
        deleteConfiguration: operations.deleteConfiguration,
        handleKeyDown: dropdown.handleKeyDown,
        handleChange,
        handleFocus,
        handleBlur,
        exportToDefaults: operations.exportToDefaults,
        setHighlightIndex: dropdown.setHighlightIndex,
        confirmModal: {
            isOpen: confirmModal.isOpen,
            message: confirmModal.message,
            onConfirm: confirmModal.handleConfirm,
            close: confirmModal.close,
        },
        savedConfigs,
        savedConfigName,
        toggleNotification,
        toggleStatistics,
        togglePin,
        isWatching,
        watcherResults,
        lastCheckTime,
        toggleWatch
    };
}
