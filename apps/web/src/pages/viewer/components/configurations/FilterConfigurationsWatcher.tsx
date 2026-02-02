import './FilterConfigurationsWatcher.css';
import type { WatcherResult } from './hooks/useFilterWatcher';

interface FilterConfigurationsWatcherProps {
    isWatching: boolean;
    results: Record<string, WatcherResult>;
    lastCheckTime: Date | null;
    onConfigClick: (name: string) => void;
}

export function FilterConfigurationsWatcher({
    isWatching,
    results,
    lastCheckTime,
    onConfigClick
}: FilterConfigurationsWatcherProps) {
    if (!isWatching) return null;

    const noResults = Object.keys(results).length === 0;

    return (
        <div className="filter-watcher-badges">
            {noResults && (
                <div className="watcher-loading-badge">Initializing...</div>
            )}
            {Object.entries(results).map(([name, result]) => (
                <div 
                    key={name} 
                    className={`watcher-badge ${result.newItems > 0 ? 'has-new' : ''}`} 
                    title={`Total: ${result.total} | New: ${result.newItems} | Last check: ${lastCheckTime?.toLocaleTimeString()}`}
                    onClick={() => onConfigClick(name)}
                >
                    <span className="badge-name">{name}</span>
                    <span className="badge-count">+{result.newItems}</span>
                </div>
            ))}
        </div>
    );
}
