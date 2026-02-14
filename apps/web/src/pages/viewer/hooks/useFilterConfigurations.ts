import { useState, useEffect, useRef } from 'react';
import type { JobListParams } from '../api/ViewerApi';
import { persistenceApi } from '../../common/api/CommonPersistenceApi';
import { BOOLEAN_FILTERS } from '../constants';
import { useFilterDropdown } from './useFilterDropdown';
import { useConfirmationModal } from '../../common/hooks/useConfirmationModal';

import defaultFilterConfigurations from '../../../resources/defaultFilterConfigurations.json';

export interface FilterConfig {
    name: string;
    filters: JobListParams;
}

const STORAGE_KEY = 'filter_configurations';
const MAX_CONFIGS = 30;

interface UseFilterConfigurationsProps {
    currentFilters: JobListParams;
    onLoadConfig: (filters: JobListParams, name: string) => void;
    onMessage?: (message: string, type: 'success' | 'error') => void;
    additionalDefaults?: FilterConfig[];
}

export function useFilterConfigurations({ currentFilters, onLoadConfig, onMessage, additionalDefaults = [] }: UseFilterConfigurationsProps) {
    const [configName, setConfigName] = useState('');
    const [savedConfigs, setSavedConfigs] = useState<FilterConfig[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [savedConfigName, setSavedConfigName] = useState(''); 
    const confirmModal = useConfirmationModal();
    const isMounted = useRef(true);

    // Load saved configurations
    useEffect(() => {
        isMounted.current = true;
        const loadConfigs = async () => {
            const stored = await persistenceApi.getValue<FilterConfig[]>(STORAGE_KEY);
            let configs = stored && Array.isArray(stored) ? stored : [];
            // Merge defaults if not present
            const allDefaults = [...defaultFilterConfigurations, ...(additionalDefaults || [])];
            const defaultsToAdd = allDefaults.filter(d => !configs.some(c => c.name === d.name));
            if (defaultsToAdd.length > 0) {
                configs = [...configs, ...defaultsToAdd];
            }
            if (isMounted.current) {
                setSavedConfigs(configs);
            }
        };
        loadConfigs();
        return () => { isMounted.current = false; };
    }, [additionalDefaults]);

    const saveConfiguration = async () => {
        if (!configName.trim()) {
            notify('Please enter a name for the configuration', 'error');
            return;
        }
        const newConfig: FilterConfig = {
            name: configName.trim(),
            filters: currentFilters,
        };
        const filtered = savedConfigs.filter(c => c.name !== newConfig.name);
        const updated = [newConfig, ...filtered].slice(0, MAX_CONFIGS);
        if (await persistConfigs(updated)) {
            setSavedConfigs(updated);
            setConfigName('');
            setIsOpen(false);
            notify(`Configuration "${newConfig.name}" saved!`, 'success');
        }
    };

    const loadConfiguration = (config: FilterConfig) => {
        resetBooleanFilters(config);
        onLoadConfig(config.filters, config.name);
        setConfigName(config.name);
        setSavedConfigName(config.name);
        setIsOpen(false);
        // We might need to reset highlight index in the dropdown hook, but we don't have access to setHighlightIndex directly here unless we pass it or expose a reset.
        // The dropdown hook manages its own highlight state based on filteredConfigs which might change. 
        // Ideally the dropdown closes and resets state on re-open.
    };

    const deleteConfiguration = async (name: string, event: React.MouseEvent) => {
        event.stopPropagation();
        confirmModal.confirm(`Delete configuration "${name}"?`, async () => {
            const updated = savedConfigs.filter(c => c.name !== name);
            if (await persistConfigs(updated)) {
                setSavedConfigs(updated);
            }
        });
    };

    const persistConfigs = async (configs: FilterConfig[]) => {
        try {
            await persistenceApi.setValue(STORAGE_KEY, configs);
            return true;
        } catch (e) {
            console.error("Failed to save configuration", e);
            notify("Failed to save configuration", "error");
            return false;
        }
    };

    const notify = (msg: string, type: 'success' | 'error') => {
        if (onMessage) onMessage(msg, type);
        else console.warn(`Message (${type}): ${msg}`);
    };

    const { 
        highlightIndex, 
        setHighlightIndex, 
        wrapperRef, 
        filteredConfigs, 
        handleKeyDown 
    } = useFilterDropdown({
        configs: savedConfigs,
        configName,
        onLoad: loadConfiguration,
        onSave: saveConfiguration,
        onDelete: deleteConfiguration,
        setIsOpen,
        isOpen
    });
    
    // Reset highlight when closing
    useEffect(() => {
        if (!isOpen) setHighlightIndex(-1);
    }, [isOpen, setHighlightIndex]);


    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setConfigName(e.target.value);
        if (!isOpen) setIsOpen(true);
        setHighlightIndex(-1);
    };

    const handleFocus = () => {
        if (savedConfigName && configName === savedConfigName) {
            setConfigName('');
        }
        setIsOpen(true);
    };

    const handleBlur = () => {
        setTimeout(() => {
            if (!configName && savedConfigName) {
                setConfigName(savedConfigName);
            }
            setIsOpen(false);
        }, 200);
    };

    const exportToDefaults = async () => {
        const stored = await persistenceApi.getValue<FilterConfig[]>(STORAGE_KEY);
        if (!stored || stored.length === 0) {
            notify('No configurations to export.', 'error');
            return;
        }
        const jsonString = JSON.stringify(stored, null, 4);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'defaultFilterConfigurations.json';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        notify('Configuration downloaded!', 'success');
    };

    const resetBooleanFilters = (config: FilterConfig) => BOOLEAN_FILTERS
            .filter(entry => !(entry.key in config.filters))
            .forEach(entry => (config.filters as any)[entry.key] = null);

    return {
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
        confirmModal: {
            isOpen: confirmModal.isOpen,
            message: confirmModal.message,
            onConfirm: confirmModal.handleConfirm,
            close: confirmModal.close,
        }
    };
}