import type { FilterConfig } from './hooks/useFilterConfigurations';
import type { WatcherResult } from './hooks/useFilterWatcher';
import { useState } from 'react';

interface PinnedConfigurationsProps {
    pinnedConfigs: FilterConfig[];
    onLoad: (config: FilterConfig) => void;
    onUnpin: (name: string) => void;
    results?: Record<string, WatcherResult>;
    selectedConfigName?: string;
}

export function PinnedConfigurations({ pinnedConfigs, onLoad, onUnpin, results = {}, selectedConfigName }: PinnedConfigurationsProps) {
    const [collapsed, setCollapsed] = useState(false);
    if (pinnedConfigs.length === 0) {
        return null;
    }
    const watchedConfigs = pinnedConfigs.filter(c => c.watched);
    const hasWatched = watchedConfigs.length > 0;
    return (
        <div className="pinned-configurations">
            <button
                className="pinned-collapse-btn"
                onClick={() => setCollapsed(c => !c)}
                title={collapsed ? "Expand watched filters" : "Collapse watched filters"}
            >
                {collapsed ? '▶' : '▼'} Watched {hasWatched && `(${watchedConfigs.length})`}
            </button>
            {!collapsed && pinnedConfigs.map((config) => {
                const result = results[config.name];
                const hasNew = result && result.newItems > 0;
                const isSelected = config.name === selectedConfigName;
                return (
                    <div key={config.name} className={`pinned-config-item ${isSelected ? 'selected' : ''} ${config.watched ? 'is-watched' : ''}`}>
                        <button
                            className="pinned-config-load"
                            onClick={() => onLoad(config)}
                            title={`Load: ${config.name}`}
                        >
                            <span className="pinned-config-name text-no-wrap">
                                {config.name}
                                {hasNew && <span className="watcher-badge-inline">+{result.newItems}</span>}
                            </span>
                            <span className="pinned-config-badges">
                                {config.statistics !== false && <span title="Included in Statistics">📈</span>}
                                {config.watched && <span title="Watched">🔔</span>}
                            </span>
                        </button>
                        <button
                            className="pinned-config-unpin"
                            onClick={() => onUnpin(config.name)}
                            title="Unpin"
                        >
                            ×
                        </button>
                    </div>
                );
            })}
        </div>
    );
}
