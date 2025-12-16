import { useState, useEffect, useRef } from 'react';
import type { JobListParams } from '../api/jobs';
import { persistenceApi } from '../api/persistence';

export interface FilterConfig {
    name: string;
    filters: JobListParams;
}

const STORAGE_KEY = 'filter_configurations';
const MAX_CONFIGS = 30;

interface UseFilterConfigurationsProps {
    currentFilters: JobListParams;
    onLoadConfig: (filters: JobListParams) => void;
    onMessage?: (message: string, type: 'success' | 'error') => void;
}

export function useFilterConfigurations({ currentFilters, onLoadConfig, onMessage }: UseFilterConfigurationsProps) {
    const [configName, setConfigName] = useState('');
    const [savedConfigs, setSavedConfigs] = useState<FilterConfig[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [highlightIndex, setHighlightIndex] = useState(-1);
    const [savedConfigName, setSavedConfigName] = useState(''); 
    const wrapperRef = useRef<HTMLDivElement>(null);

    // Load saved configurations
    useEffect(() => {
        const loadConfigs = async () => {
            const stored = await persistenceApi.getValue<FilterConfig[]>(STORAGE_KEY);
            if (stored && Array.isArray(stored)) {
                setSavedConfigs(stored);
            }
        };
        loadConfigs();
    }, []);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [isOpen]);

    const filteredConfigs = savedConfigs.filter(config =>
        config.name.toLowerCase().includes((configName || '').toLowerCase())
    );

    const saveConfiguration = async () => {
        if (!configName.trim()) {
            if (onMessage) {
                onMessage('Please enter a name for the configuration', 'error');
            } else {
                alert('Please enter a name for the configuration');
            }
            return;
        }

        const newConfig: FilterConfig = {
            name: configName.trim(),
            filters: currentFilters,
        };

        const filtered = savedConfigs.filter(c => c.name !== newConfig.name);
        const updated = [newConfig, ...filtered].slice(0, MAX_CONFIGS);
        
        setSavedConfigs(updated);

        try {
            await persistenceApi.setValue(STORAGE_KEY, updated);
            setConfigName('');
            setIsOpen(false);
            if (onMessage) {
               onMessage(`Configuration "${newConfig.name}" saved!`, 'success');
            }
        } catch (e) {
            console.error("Failed to save configuration", e);
            if (onMessage) onMessage("Failed to save configuration", "error");
        }
    };

    const loadConfiguration = (config: FilterConfig) => {
        onLoadConfig(config.filters);
        setConfigName(config.name);
        setSavedConfigName(config.name);
        setIsOpen(false);
        setHighlightIndex(-1);
    };

    const deleteConfiguration = async (name: string, event: React.MouseEvent) => {
        event.stopPropagation();
        if (confirm(`Delete configuration "${name}"?`)) {
            const updated = savedConfigs.filter(c => c.name !== name);
            setSavedConfigs(updated);
            
            try {
                await persistenceApi.setValue(STORAGE_KEY, updated);
            } catch (e) {
                console.error("Failed to delete configuration", e);
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (!isOpen) {
                setIsOpen(true);
            } else {
                setHighlightIndex(prev =>
                    prev < filteredConfigs.length - 1 ? prev + 1 : prev
                );
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (isOpen) {
                setHighlightIndex(prev => prev > 0 ? prev - 1 : -1);
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (isOpen && highlightIndex >= 0 && highlightIndex < filteredConfigs.length) {
                loadConfiguration(filteredConfigs[highlightIndex]);
            } else {
                saveConfiguration();
            }
        } else if (e.key === 'Escape') {
            setIsOpen(false);
            setHighlightIndex(-1);
        } else if (e.key === 'Delete') {
            if (isOpen && highlightIndex >= 0 && highlightIndex < filteredConfigs.length) {
                e.preventDefault();
                const configToDelete = filteredConfigs[highlightIndex];
                deleteConfiguration(configToDelete.name, e as any);
                if (highlightIndex >= filteredConfigs.length - 1) {
                    setHighlightIndex(Math.max(-1, filteredConfigs.length - 2));
                }
            }
        }
    };

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
            if (onMessage) onMessage('No configurations to export.', 'error');
            return;
        }

        const exportString = `// Paste this into apps/web/src/data/defaults.ts\nexport const defaultFilterConfigurations = ${JSON.stringify(stored, null, 4)};`;
        
        try {
            await navigator.clipboard.writeText(exportString);
            if (onMessage) {
                onMessage('Configuration copied to clipboard! Paste into defaults.ts', 'success');
            }
        } catch (err) {
            console.error('Failed to copy', err);
            if (onMessage) onMessage('Failed to copy to clipboard. Check console.', 'error');
            console.log(exportString);
        }
    };

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
        setHighlightIndex
    };
}
