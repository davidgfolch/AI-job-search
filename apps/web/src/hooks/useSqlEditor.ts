import { useState, useEffect, useCallback } from 'react';
import { fetchDdlSchema } from '../api/ddl';
import { Suggestion, getCaretCoordinates } from '../utils/sqlEditorUtils';

interface UseSqlEditorProps {
    isOpen: boolean;
    initialValue: string;
    textareaRef: React.RefObject<HTMLTextAreaElement>;
}

export const useSqlEditor = ({ isOpen, initialValue, textareaRef }: UseSqlEditorProps) => {
    const [value, setValue] = useState(initialValue);
    const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
    const [schema, setSchema] = useState<Record<string, string[]>>({});
    const [keywords, setKeywords] = useState<string[]>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const [suggestionIndex, setSuggestionIndex] = useState(0);
    const [cursorPosition, setCursorPosition] = useState({ top: 0, left: 0 });

    useEffect(() => {
        if (isOpen) {
            setValue(initialValue);
            fetchDdlSchema().then(data => {
                setSchema(data.tables);
                setKeywords(data.keywords);
            }).catch(console.error);
        }
    }, [isOpen, initialValue]);

    const updateSuggestions = useCallback((text: string, cursorIndex: number) => {
        // Find the word being typed
        const left = text.slice(0, cursorIndex);
        const match = left.match(/([a-zA-Z0-9_.]+)$/);
        if (!match) {
            setShowSuggestions(false);
            return;
        }
        const currentWord = match[1];
        const lowerWord = currentWord.toLowerCase();
        let newSuggestions: Suggestion[] = [];
        // Check for table.column pattern
        if (currentWord.includes('.')) {
            const [tableName, colPrefix] = currentWord.split('.');
            if (schema[tableName]) {
                const availableCols = schema[tableName];
                 newSuggestions = availableCols
                    .filter(col => col.toLowerCase().startsWith(colPrefix.toLowerCase()))
                    .map(col => ({ text: col, type: 'column' }));
            }
        } else {
            // Suggest keywords and tables
            const matchedKeywords = keywords
                .filter(k => k.toLowerCase().startsWith(lowerWord))
                .map(k => ({ text: k, type: 'keyword' } as Suggestion));
            const matchedTables = Object.keys(schema)
                .filter(t => t.toLowerCase().startsWith(lowerWord))
                .map(t => ({ text: t, type: 'table' } as Suggestion));
            newSuggestions = [...matchedKeywords, ...matchedTables];
        }
        if (newSuggestions.length > 0) {
            setSuggestions(newSuggestions);
            setShowSuggestions(true);
            setSuggestionIndex(0);
            
            if (textareaRef.current) {
                 const { top, left } = getCaretCoordinates(textareaRef.current, cursorIndex);
                 setCursorPosition({ top: top + 20, left });
            }
        } else {
            setShowSuggestions(false);
        }
    }, [schema, keywords, textareaRef]);

    const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newValue = e.target.value;
        setValue(newValue);
        updateSuggestions(newValue, e.target.selectionStart);
    }, [updateSuggestions]);

    const applySuggestion = useCallback((suggestion: Suggestion) => {
        if (!textareaRef.current) return;
        const cursorIndex = textareaRef.current.selectionStart;
        const text = value;
        const left = text.slice(0, cursorIndex);
        const right = text.slice(cursorIndex);
        const match = left.match(/([a-zA-Z0-9_.]+)$/);
        if (match) {
            const currentWord = match[1];
            let insertion = suggestion.text;
            if (currentWord.includes('.')) {
                 const prefixTable = currentWord.split('.')[0];
                 const newValue = text.slice(0, cursorIndex - currentWord.length) + prefixTable + '.' + insertion + right;
                 setValue(newValue);
            } else {
                 const newValue = text.slice(0, cursorIndex - currentWord.length) + insertion + right;
                 setValue(newValue);
            }
            setShowSuggestions(false);
            // Focus and cursor position would ideally be handled here too if possible
        }
    }, [textareaRef, value]);

    const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
        if (showSuggestions) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSuggestionIndex(prev => (prev + 1) % suggestions.length);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSuggestionIndex(prev => (prev - 1 + suggestions.length) % suggestions.length);
            } else if (e.key === 'Enter' || e.key === 'Tab') {
                e.preventDefault();
                applySuggestion(suggestions[suggestionIndex]);
            } else if (e.key === 'Escape') {
                setShowSuggestions(false);
            }
        }
    }, [showSuggestions, suggestions, suggestionIndex, applySuggestion]);

    return {
        value,
        suggestions,
        schema,
        keywords,
        showSuggestions,
        suggestionIndex,
        cursorPosition,
        handleChange,
        handleKeyDown,
        applySuggestion
    };
};
