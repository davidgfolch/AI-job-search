import type { FilterConfig } from './hooks/useFilterConfigurations';
import type { WatcherResult } from './hooks/useFilterWatcher';

interface PinnedConfigurationsProps {
    pinnedConfigs: FilterConfig[];
    onLoad: (config: FilterConfig) => void;
    onUnpin: (name: string) => void;
    results?: Record<string, WatcherResult>;
    selectedConfigName?: string;
}

export function PinnedConfigurations({ pinnedConfigs, onLoad, onUnpin, results = {}, selectedConfigName }: PinnedConfigurationsProps) {
    if (pinnedConfigs.length === 0) {
        return null;
    }
    return (
        <div className="pinned-configurations">
            {pinnedConfigs.map((config) => {
                const result = results[config.name];
                const hasNew = result && result.newItems > 0;
                const isSelected = config.name === selectedConfigName;
                return (
                    <div key={config.name} className={`pinned-config-item ${isSelected ? 'selected' : ''}`}>
                        <button
                            className="pinned-config-load"
                            onClick={() => onLoad(config)}
                            title={`Load: ${config.name}`}
                        >
                            <span className="pinned-config-name">
                                {config.name}
                                {hasNew && <span className="watcher-badge-inline">+{result.newItems}</span>}
                            </span>
                            <span className="pinned-config-badges">
                                {config.statistics !== false && <span title="Included in Statistics">📈</span>}
                                {config.notify && <span title="Notifications enabled">🔔</span>}
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
