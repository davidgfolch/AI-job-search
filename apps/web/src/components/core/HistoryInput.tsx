import React, { useState, useEffect, useRef } from 'react';
import { persistenceApi } from '../../api/persistence';
import './HistoryInput.css';

interface HistoryInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    storageKey: string;
    value: string;
    onValueChange: (value: string) => void;
}

export default function HistoryInput({
    storageKey,
    value,
    onValueChange,
    onBlur,
    onKeyDown,
    onFocus,
    className,
    ...props
}: HistoryInputProps) {
    const [history, setHistory] = useState<string[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [highlightIndex, setHighlightIndex] = useState(-1);
    const wrapperRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const loadHistory = async () => {
             const stored = await persistenceApi.getValue<string[]>(storageKey);
             if (stored && Array.isArray(stored)) {
                 setHistory(stored);
             }
        };
        loadHistory();
    }, [storageKey]);

    const addToHistory = async (val: string) => {
        if (!val || val.trim() === '') return;
        const trimmed = val.trim();

        // Optimistically update
        const newHistory = [trimmed, ...history.filter(h => h !== trimmed)].slice(0, 20);
        setHistory(newHistory);
        
        try {
            await persistenceApi.setValue(storageKey, newHistory);
        } catch (e) {
            console.error('Failed to save history', e);
            // Optionally revert on error, but simple logging is likely enough for now
        }
    };

    const removeFromHistory = async (val: string) => {
        // Optimistically update
        const newHistory = history.filter(h => h !== val);
        setHistory(newHistory);
        
        try {
           await persistenceApi.setValue(storageKey, newHistory);
        } catch (e) {
           console.error('Failed to remove from history', e);
        }
    };

    const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
        // Delay closing to allow click on suggestion to register
        // But cleaner way is using mousedown on item effectively

        // Also save text to history on blur if it has content
        if (value) {
            addToHistory(value);
        }

        if (onBlur) onBlur(e);

        // We need to close the menu, but if we just setIsOpen(false) here, 
        // the click on the item won't fire.
        // We handle closing via document click or timeout, 
        // or relying on the fact that item click will happen before blur?
        // Actually, item click -> mousedown -> blur -> click. 
        // So mousedown on item should prevent default or we just use a small timeout.
        setTimeout(() => setIsOpen(false), 200);
    };

    const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
        setIsOpen(true);
        if (onFocus) onFocus(e);
    };

    const filteredHistory = history.filter(item =>
        item.toLowerCase().includes((value || '').toLowerCase())
    );


    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (!isOpen) {
                setIsOpen(true);
            } else {
                setHighlightIndex(prev =>
                    prev < filteredHistory.length - 1 ? prev + 1 : prev
                );
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (isOpen) {
                setHighlightIndex(prev => prev > 0 ? prev - 1 : -1);
            }
        } else if (e.key === 'Enter') {
            if (isOpen && highlightIndex >= 0 && highlightIndex < filteredHistory.length) {
                e.preventDefault();
                const selected = filteredHistory[highlightIndex];
                onValueChange(selected);
                setIsOpen(false);
                setHighlightIndex(-1);
            } else {
                // Normal enter, save to history
                addToHistory(value);
                setIsOpen(false);
            }
        } else if (e.key === 'Escape') {
            setIsOpen(false);
        } else if (e.key === 'Delete') {
            if (isOpen && highlightIndex >= 0 && highlightIndex < filteredHistory.length) {
                e.preventDefault();
                const itemToDelete = filteredHistory[highlightIndex];
                removeFromHistory(itemToDelete);
                // Adjust highlight index if needed
                if (highlightIndex >= filteredHistory.length - 1) {
                    setHighlightIndex(Math.max(-1, filteredHistory.length - 2));
                }
            }
        }

        if (onKeyDown) onKeyDown(e);
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        onValueChange(e.target.value);
        if (!isOpen) setIsOpen(true);
        setHighlightIndex(-1);
    };

    return (
        <div className="history-input-wrapper" ref={wrapperRef}>
            <input
                {...props}
                value={value}
                onChange={handleChange}
                onBlur={handleBlur}
                onFocus={handleFocus}
                onKeyDown={handleKeyDown}
                className={className}
                autoComplete="off"
            />
            {isOpen && filteredHistory.length > 0 && (
                <ul className="history-suggestions">
                    {filteredHistory.map((item, index) => (
                        <li
                            key={item}
                            className={`history-suggestion-item ${index === highlightIndex ? 'active' : ''}`}
                            onMouseDown={(e) => {
                                // Prevent blur so click works
                                e.preventDefault();
                            }}
                            onClick={() => {
                                onValueChange(item);
                                setIsOpen(false);
                                setHighlightIndex(-1);
                            }}
                            onMouseEnter={() => setHighlightIndex(index)}
                        >
                            {item}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
