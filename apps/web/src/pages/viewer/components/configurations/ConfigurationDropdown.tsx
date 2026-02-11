import React from 'react';
import type { WatcherResult } from './hooks/useFilterWatcher.types';
import type { FilterConfig } from './hooks/useFilterConfigurations';

interface ConfigurationDropdownProps {
    isOpen: boolean;
    filteredConfigs: FilterConfig[];
    highlightIndex: number;
    onLoad: (config: FilterConfig) => void;
    onDelete: (name: string, event: React.MouseEvent) => void;
    setHighlightIndex: (index: number) => void;
    onToggleNotify: (name: string) => void;
    onToggleStats: (name: string) => void;
    onTogglePin: (name: string) => void;
    results?: Record<string, WatcherResult>;
    lastCheckTime?: Date | null;
}

export function ConfigurationDropdown({
    isOpen,
    filteredConfigs,
    highlightIndex,
    onLoad,
    onDelete,
    setHighlightIndex,
    onToggleNotify,
    onToggleStats,
    onTogglePin,
    results = {},
    lastCheckTime
}: ConfigurationDropdownProps) {
    if (!isOpen || filteredConfigs.length === 0) {
        return null;
    }

    return (
        <ul className="config-suggestions">
            {filteredConfigs.map((config, index) => {
                const result = results[config.name];
                const hasNew = result && result.newItems > 0;
                
                return (
                <li
                    key={config.name}
                    className={`config-suggestion-item ${index === highlightIndex ? 'active' : ''}`}
                    onMouseDown={(e) => {
                        e.preventDefault(); // Prevent blur
                    }}
                    onClick={() => onLoad(config)}
                    onMouseEnter={() => setHighlightIndex(index)}
                    title={result ? `Total: ${result.total} | New: ${result.newItems} | Last check: ${lastCheckTime?.toLocaleTimeString()}` : undefined}
                >
                    <span className="config-name text-no-wrap">
                        {config.name}
                        {hasNew && <span className="watcher-badge-inline">+{result.newItems}</span>}
                    </span>
                    <button
                        className={`config-toggle-btn ${config.pinned ? 'enabled' : 'disabled'}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            onTogglePin(config.name);
                        }}
                        title={config.pinned ? "Unpin configuration" : "Pin configuration"}
                        onMouseDown={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                        }}
                    >
                        📌
                    </button>
                    <button
                        className={`config-toggle-btn ${config.statistics !== false ? 'enabled' : 'disabled'}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            onToggleStats(config.name);
                        }}
                        title={config.statistics == false ? "Include in Statistics" : "Exclude from Statistics"}
                        onMouseDown={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                        }}
                    >
                        {config.statistics !== false ? '📈' : '📉'}
                    </button>
                    <button 
                        className={`config-toggle-btn ${config.notify ? 'enabled' : 'disabled'}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            onToggleNotify(config.name);
                        }}
                        title={config.notify ? "Disable notifications" : "Enable notifications"}
                        onMouseDown={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                        }}
                    >
                        {config.notify ? '🔔' : '🔕'}
                    </button>
                    <button
                        type="button"
                        onMouseDown={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                        }}
                        onClick={(e) => onDelete(config.name, e)}
                        className="config-delete-btn"
                        title="Delete configuration"
                    >
                        ×
                    </button>
                </li>
            )})}
        </ul>
    );
}
