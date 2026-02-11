import React, { useRef } from 'react';
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
    onReorder?: (configs: FilterConfig[]) => void;
    allowReorder?: boolean;
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
    lastCheckTime,
    onReorder,
    allowReorder = false
}: ConfigurationDropdownProps) {
    const dragItem = useRef<number | null>(null);
    const dragOverItem = useRef<number | null>(null);

    if (!isOpen || filteredConfigs.length === 0) {
        return null;
    }

    const handleDragStart = (e: React.DragEvent<HTMLLIElement>, index: number) => {
        dragItem.current = index;
        e.dataTransfer.effectAllowed = "move";
        // e.target.style.opacity = '0.5'; // Optional visual feedback
    };

    const handleDragEnter = (e: React.DragEvent<HTMLLIElement>, index: number) => {
        dragOverItem.current = index;
        e.preventDefault();
    };

    const handleDragOver = (e: React.DragEvent<HTMLLIElement>) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
    };

    const handleDrop = (e: React.DragEvent<HTMLLIElement>) => {
        e.preventDefault();
        const fromIndex = dragItem.current;
        const toIndex = dragOverItem.current;
        
        if (fromIndex !== null && toIndex !== null && fromIndex !== toIndex && onReorder) {
            const copyListItems = [...filteredConfigs];
            const [reorderedItem] = copyListItems.splice(fromIndex, 1);
            copyListItems.splice(toIndex, 0, reorderedItem);
            onReorder(copyListItems);
        }
        
        dragItem.current = null;
        dragOverItem.current = null;
    };

    return (
        <ul className="config-suggestions">
            {filteredConfigs.map((config, index) => {
                const result = results[config.name];
                const hasNew = result && result.newItems > 0;
                
                return (
                <li
                    key={config.name}
                    className={`config-suggestion-item ${index === highlightIndex ? 'active' : ''}`}
                    tabIndex={-1}
                    style={{ outline: 'none' }}
                    onMouseDown={() => {
                        // Allow default for drag and drop to work.
                        // We handle focus/blur in the parent component to prevent closing on interaction.
                    }}
                    onClick={() => onLoad(config)}
                    onMouseEnter={() => setHighlightIndex(index)}
                    title={result ? `Total: ${result.total} | New: ${result.newItems} | Last check: ${lastCheckTime?.toLocaleTimeString()}` : undefined}
                    draggable={allowReorder}
                    onDragStart={(e) => handleDragStart(e, index)}
                    onDragEnter={(e) => handleDragEnter(e, index)}
                    onDragOver={handleDragOver}
                    onDrop={handleDrop}
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
