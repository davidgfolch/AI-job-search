import { useState, useRef, useEffect } from 'react';
import type { FilterConfig } from '../components/configurations/hooks/useFilterConfigurations';

interface UseFilterDropdownProps {
    configs: FilterConfig[];
    configName: string;
    onLoad: (config: FilterConfig) => void;
    onSave: () => void;
    onDelete: (name: string, event: React.MouseEvent) => void;
    setIsOpen: (isOpen: boolean) => void;
    isOpen: boolean;
}

export function useFilterDropdown({ 
    configs, 
    configName, 
    onLoad, 
    onSave, 
    onDelete,
    setIsOpen,
    isOpen
}: UseFilterDropdownProps) {
    const [highlightIndex, setHighlightIndex] = useState(-1);
    const wrapperRef = useRef<HTMLDivElement>(null);

    const filteredConfigs = configs.filter(config =>
        config.name.toLowerCase().includes((configName || '').toLowerCase())
    ).sort((a, b) => a.name.localeCompare(b.name));

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
    }, [isOpen, setIsOpen]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (!isOpen) {
                setIsOpen(true);
            } else {
                setHighlightIndex(prev => prev < filteredConfigs.length - 1 ? prev + 1 : prev);
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (isOpen) {
                setHighlightIndex(prev => prev > 0 ? prev - 1 : -1);
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (isOpen && highlightIndex >= 0 && highlightIndex < filteredConfigs.length) {
                onLoad(filteredConfigs[highlightIndex]);
            } else {
                onSave();
            }
        } else if (e.key === 'Escape') {
            setIsOpen(false);
            setHighlightIndex(-1);
        } else if (e.key === 'Delete') {
            if (isOpen && highlightIndex >= 0 && highlightIndex < filteredConfigs.length) {
                e.preventDefault();
                const configToDelete = filteredConfigs[highlightIndex];
                onDelete(configToDelete.name, e as any);
                if (highlightIndex >= filteredConfigs.length - 1) {
                    setHighlightIndex(Math.max(-1, filteredConfigs.length - 2));
                }
            }
        }
    };

    return {
        highlightIndex,
        setHighlightIndex,
        wrapperRef,
        filteredConfigs,
        handleKeyDown
    };
}
