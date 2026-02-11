import { useState, useRef, useEffect } from 'react';
import type { FilterConfig } from './useFilterConfigurations';


interface UseFilterDropdownProps {
    configs: FilterConfig[];
    configName: string;
    onLoad: (config: FilterConfig) => void;
    onSave: () => void;
    onDelete: (name: string, event: React.MouseEvent) => void;
    setIsOpen: (isOpen: boolean) => void;
    isOpen: boolean;
    results?: Record<string, { newItems: number; total: number }>;
}

export function useFilterDropdown({ 
    configs, 
    configName, 
    onLoad, 
    onSave, 
    onDelete,
    setIsOpen,
    isOpen,
    results
}: UseFilterDropdownProps) {
    const [highlightIndex, setHighlightIndex] = useState(-1);
    const wrapperRef = useRef<HTMLDivElement>(null);

    const filteredConfigs = configs
        .filter(config =>
            config.name.toLowerCase().includes((configName || '').toLowerCase())
        )
        .sort((a, b) => {
            // Priority 0: Explicit Ordering (from drag-and-drop)
            const hasOrdering = a.ordering !== undefined || b.ordering !== undefined;
            if (hasOrdering) {
                const aOrder = a.ordering ?? Number.MAX_SAFE_INTEGER;
                const bOrder = b.ordering ?? Number.MAX_SAFE_INTEGER;
                return aOrder - bOrder;
            }

            // Priority 1: New Items (if results exist)
            const aNew = results?.[a.name]?.newItems ?? 0;
            const bNew = results?.[b.name]?.newItems ?? 0;
            if (aNew > 0 && bNew === 0) return -1;
            if (bNew > 0 && aNew === 0) return 1;
            if (aNew > 0 && bNew > 0 && aNew !== bNew) return bNew - aNew;

            // Priority 2: Watched
            if (a.watched && !b.watched) return -1;
            if (b.watched && !a.watched) return 1;

            // Priority 3: Statistics
            if (a.statistics && !b.statistics) return -1;
            if (b.statistics && !a.statistics) return 1;

            // Priority 4: Name (Alphabetical)
            return a.name.localeCompare(b.name);
        });

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
