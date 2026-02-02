import React from 'react';

interface ConfigurationInputProps {
    configName: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
    onFocus: () => void;
    onClick: () => void;
    onBlur: () => void;
    onSave: () => void;
    onExport: () => void;
    onWatch: () => void;
    isWatching: boolean;
}

export function ConfigurationInput({
    configName,
    onChange,
    onKeyDown,
    onFocus,
    onClick,
    onBlur,
    onSave,
    onExport,
    onWatch,
    isWatching
}: ConfigurationInputProps) {
    if (isWatching) {
        return (
            <button
                type="button"
                onClick={onWatch}
                className="config-btn config-watch-btn active"
                title="Stop watching filter configurations"
            >
                Stop Watch
            </button>
        );
    }

    return (
        <>
            <input
                id="filter-config-input"
                type="text"
                placeholder="Type to load or enter name to save..."
                value={configName}
                onChange={onChange}
                onKeyDown={onKeyDown}
                onFocus={onFocus}
                onClick={onClick}
                onBlur={onBlur}
                className="config-input"
                autoComplete="off"
            />
            <button
                type="button"
                onClick={onSave}
                className="config-btn"
                title="Save current filters with the name above"
            >
                Save
            </button>
            <button
                type="button"
                onClick={onExport}
                className="config-btn config-export-btn"
                title="Copy configurations to clipboard for defaults.ts"
            >
                Export
            </button>
            <button
                type="button"
                onClick={onWatch}
                className="config-btn config-watch-btn"
                title="Watch all filter configurations for new items (every 5 min)"
            >
                Watch
            </button>
        </>
    );
}
