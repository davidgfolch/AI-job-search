import { useState, useEffect, useMemo, useCallback } from 'react';
import type { JobListParams } from '../../../api/ViewerApi';
import defaultFilterConfigurations from '../../../../../resources/defaultFilterConfigurations.json';
import { FilterConfigService } from '../../../hooks/FilterConfigService';
import { useFilterDropdown } from './useFilterDropdown';
import { useConfirmationModal } from './useConfirmationModal';
import { useConfigDropdownState } from './useConfigDropdownState';
import { useConfigOperations } from './useConfigOperations';

export interface FilterConfig {
    name: string;
    filters: JobListParams;
    notify?: boolean;
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

    useEffect(() => {
        const loadConfigs = async () => {
            try {
                const allDefaults = [...(defaultFilterConfigurations as any[]), ...additionalDefaults];
                const configs = await service.load(allDefaults);
                setSavedConfigs(configs);
            } catch (e) {
                console.error('Failed to load configurations', e);
                notify('Failed to load configurations', 'error');
            }
        };
        loadConfigs();
    }, [service, additionalDefaults, notify]);

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

    const toggleNotification = useCallback(async (name: string) => {
        const configIndex = savedConfigs.findIndex(c => c.name === name);
        if (configIndex === -1) return;

        const updatedConfigs = [...savedConfigs];
        updatedConfigs[configIndex] = {
            ...updatedConfigs[configIndex],
            notify: !updatedConfigs[configIndex].notify
        };

        try {
            await service.save(updatedConfigs);
            setSavedConfigs(updatedConfigs);
        } catch (e) {
            console.error('Failed to save configuration', e);
            notify('Failed to update notification setting', 'error');
        }
    }, [savedConfigs, service, notify]);

    const dropdown = useFilterDropdown({
        configs: savedConfigs,
        configName,
        onLoad: operations.loadConfiguration,
        onSave: operations.saveConfiguration,
        onDelete: operations.deleteConfiguration,
        setIsOpen,
        isOpen,
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
        loadConfiguration: operations.loadConfiguration,
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
        toggleNotification,
    };
}
