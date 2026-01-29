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
}

export function ConfigurationInput({
    configName,
    onChange,
    onKeyDown,
    onFocus,
    onClick,
    onBlur,
    onSave,
    onExport
}: ConfigurationInputProps) {
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
        </>
    );
}
