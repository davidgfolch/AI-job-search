import { useState, useEffect, useRef } from 'react';
import type { JobListParams } from '../api/jobs';
import { persistenceApi } from '../api/persistence';
import './FilterConfigurations.css';

interface FilterConfig {
    name: string;
    filters: JobListParams;
}

interface FilterConfigurationsProps {
    currentFilters: JobListParams;
    onLoadConfig: (filters: JobListParams) => void;
    onMessage?: (message: string, type: 'success' | 'error') => void;
}

const STORAGE_KEY = 'filter_configurations';
const MAX_CONFIGS = 30;

export default function FilterConfigurations({ currentFilters, onLoadConfig, onMessage }: FilterConfigurationsProps) {
    const [configName, setConfigName] = useState('');
    const [savedConfigs, setSavedConfigs] = useState<FilterConfig[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [highlightIndex, setHighlightIndex] = useState(-1);
    const [savedConfigName, setSavedConfigName] = useState(''); // Track the loaded config name
    const wrapperRef = useRef<HTMLDivElement>(null);

    // Load saved configurations from persistence API
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

        // Calculate new state
        const filtered = savedConfigs.filter(c => c.name !== newConfig.name);
        // Add new config at the beginning and limit to MAX_CONFIGS
        const updated = [newConfig, ...filtered].slice(0, MAX_CONFIGS);
        
        // Optimistic update
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
            // Revert could be here, strict optimistic for now
        }
    };

    const loadConfiguration = (config: FilterConfig) => {
        onLoadConfig(config.filters);
        setConfigName(config.name); // Keep the loaded config name visible
        setSavedConfigName(config.name); // Remember this as the loaded config
        setIsOpen(false);
        setHighlightIndex(-1);
    };

    const deleteConfiguration = async (name: string, event: React.MouseEvent) => {
        event.stopPropagation();
        if (confirm(`Delete configuration "${name}"?`)) {
            // Optimistic update
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
        // If there's a loaded config name, temporarily clear it to show all options
        if (savedConfigName && configName === savedConfigName) {
            setConfigName('');
        }
        setIsOpen(true);
    };

    const handleBlur = () => {
        // Delay closing to allow click on suggestion to register
        setTimeout(() => {
            // If input is empty and we had a loaded config, restore it
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

    // Filter configurations based on input
    const filteredConfigs = savedConfigs.filter(config =>
        config.name.toLowerCase().includes((configName || '').toLowerCase())
    );

    return (
        <div className="filter-configurations">
            <label htmlFor="filter-config-input">Filter Configurations:</label>
            <div className="config-controls" ref={wrapperRef}>
                <input
                    id="filter-config-input"
                    type="text"
                    placeholder="Type to load or enter name to save..."
                    value={configName}
                    onChange={handleChange}
                    onKeyDown={handleKeyDown}
                    onFocus={handleFocus}
                    onClick={handleFocus}
                    onBlur={handleBlur}
                    className="config-input"
                    autoComplete="off"
                />
                <button
                    type="button"
                    onClick={saveConfiguration}
                    className="config-save-btn"
                    title="Save current filters with the name above"
                >
                    Save
                </button>
                <button
                    type="button"
                    onClick={exportToDefaults}
                    className="config-export-btn"
                    title="Copy configurations to clipboard for defaults.ts"
                    style={{ marginLeft: '0.5rem', backgroundColor: '#4a5568' }}
                >
                    Export
                </button>
                {isOpen && filteredConfigs.length > 0 && (
                    <ul className="config-suggestions">
                        {filteredConfigs.map((config, index) => (
                            <li
                                key={config.name}
                                className={`config-suggestion-item ${index === highlightIndex ? 'active' : ''}`}
                                onMouseDown={(e) => {
                                    e.preventDefault(); // Prevent blur
                                }}
                                onClick={() => loadConfiguration(config)}
                                onMouseEnter={() => setHighlightIndex(index)}
                            >
                                <span className="config-name">{config.name}</span>
                                <button
                                    type="button"
                                    onClick={(e) => deleteConfiguration(config.name, e)}
                                    className="config-delete-btn"
                                    title="Delete configuration"
                                >
                                    ×
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}
