import './FilterConfigurationsWatcher.css';
import type { WatcherResult } from './hooks/useFilterWatcher';
import type { FilterConfig } from './hooks/useFilterConfigurations';

interface FilterConfigurationsWatcherProps {
    isWatching: boolean;
    results: Record<string, WatcherResult>;
    lastCheckTime: Date | null;
    savedConfigs: FilterConfig[];
    onConfigClick: (name: string) => void;
    onToggleNotify: (name: string) => void;
    onToggleStats: (name: string) => void;
}

export function FilterConfigurationsWatcher({
    isWatching,
    results,
    lastCheckTime,
    savedConfigs,
    onConfigClick,
    onToggleNotify,
    onToggleStats
}: FilterConfigurationsWatcherProps) {
    if (!isWatching) return null;

    const noResults = Object.keys(results).length === 0;

    return (
        <div className="filter-watcher-badges">
            {noResults && (
                <div className="watcher-loading-badge">Initializing...</div>
            )}
            {Object.entries(results)
                .sort(([nameA], [nameB]) => {
                    const configA = savedConfigs.find(c => c.name === nameA);
                    const configB = savedConfigs.find(c => c.name === nameB);
                    const notifyA = configA?.notify ? 1 : 0;
                    const notifyB = configB?.notify ? 1 : 0;
                    
                    if (notifyA !== notifyB) return notifyB - notifyA;
                    return nameA.localeCompare(nameB);
                })
                .map(([name, result]) => {
                const config = savedConfigs.find(c => c.name === name);
                const isNotifying = config?.notify;

                return (
                    <div 
                        key={name} 
                        className={`watcher-badge ${result.newItems > 0 ? 'has-new' : ''}`} 
                        title={`Total: ${result.total} | New: ${result.newItems} | Last check: ${lastCheckTime?.toLocaleTimeString()}`}
                        onClick={() => onConfigClick(name)}
                    >
                        <span className="badge-name">{name}</span>
                        <span className="badge-count">+{result.newItems}</span>
                        <div className="watcher-actions">
                            <button
                                className={`watcher-toggle ${config?.statistics !== false ? 'enabled' : 'disabled'}`}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onToggleStats(name);
                                }}
                                title={config?.statistics !== false ? "Include in Statistics" : "Exclude from Statistics"}
                            >
                                {config?.statistics !== false ? '📈' : '📉'}
                            </button>
                            <button 
                                className={`watcher-toggle ${isNotifying ? 'enabled' : 'disabled'}`}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onToggleNotify(name);
                                }}
                                title={isNotifying ? "Disable notifications" : "Enable notifications"}
                            >
                                {isNotifying ? '🔔' : '🔕'}
                            </button>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
