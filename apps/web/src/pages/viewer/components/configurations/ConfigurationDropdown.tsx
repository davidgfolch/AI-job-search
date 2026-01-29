import React from 'react';
import type { FilterConfig } from './hooks/useFilterConfigurations';

interface ConfigurationDropdownProps {
    isOpen: boolean;
    filteredConfigs: FilterConfig[];
    highlightIndex: number;
    onLoad: (config: FilterConfig) => void;
    onDelete: (name: string, event: React.MouseEvent) => void;
    setHighlightIndex: (index: number) => void;
}

export function ConfigurationDropdown({
    isOpen,
    filteredConfigs,
    highlightIndex,
    onLoad,
    onDelete,
    setHighlightIndex
}: ConfigurationDropdownProps) {
    if (!isOpen || filteredConfigs.length === 0) {
        return null;
    }

    return (
        <ul className="config-suggestions">
            {filteredConfigs.map((config, index) => (
                <li
                    key={config.name}
                    className={`config-suggestion-item ${index === highlightIndex ? 'active' : ''}`}
                    onMouseDown={(e) => {
                        e.preventDefault(); // Prevent blur
                    }}
                    onClick={() => onLoad(config)}
                    onMouseEnter={() => setHighlightIndex(index)}
                >
                    <span className="config-name">{config.name}</span>
                    <button
                        type="button"
                        onMouseDown={(e) => e.stopPropagation()}
                        onClick={(e) => onDelete(config.name, e)}
                        className="config-delete-btn"
                        title="Delete configuration"
                    >
                        ×
                    </button>
                </li>
            ))}
        </ul>
    );
}
