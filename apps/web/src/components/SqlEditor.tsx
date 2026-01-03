import React, { useRef } from 'react';
import './SqlEditor.css';
import { useSqlEditor } from '../hooks/useSqlEditor';
import { tokenizeSql } from '../utils/sqlEditorUtils';

interface SqlEditorProps {
    isOpen: boolean;
    initialValue: string;
    onSave: (value: string) => void;
    onClose: () => void;
}

export default function SqlEditor({ isOpen, initialValue, onSave, onClose }: SqlEditorProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const {
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
    } = useSqlEditor({ isOpen, initialValue, textareaRef });

    const handleScroll = (e: React.UIEvent<HTMLTextAreaElement>) => {
        // Sync scroll of highlight layer with textarea
        const highlightLayer = document.getElementById('highlight-layer');
        if (highlightLayer) {
            highlightLayer.scrollTop = e.currentTarget.scrollTop;
            highlightLayer.scrollLeft = e.currentTarget.scrollLeft;
        }
    };

    const renderHighlightedText = (text: string) => {
        if (!text) return null;
        const tokens = tokenizeSql(text, keywords, schema);
        return tokens.map((token, index) => {
             const className = token.type !== 'default' ? `highlight-${token.type}` : '';
             return className ? (
                 <span key={index} className={className}>{token.text}</span>
             ) : (
                 <span key={index}>{token.text}</span>
             );
        });
    };

    if (!isOpen) return null;

    return (
        <div className="sql-editor-overlay" onClick={onClose}>
            <div className="sql-editor-content" onClick={e => e.stopPropagation()}>
                <div className="sql-editor-header">
                    <h3>SQL Editor</h3>
                    <button className="editor-button cancel" onClick={onClose}>✕</button>
                </div>
                <div className="editor-container">
                    <div className="editor-wrapper">
                        <div id="highlight-layer" className="highlight-layer">
                            {renderHighlightedText(value)}
                             {/* Add a zero-width space or invisible char at end to fix cursor sync issues if needed, strictly textContent here */}
                             {value.endsWith('\n') && <br />}
                        </div>
                        <textarea
                            ref={textareaRef}
                            className="sql-textarea"
                            value={value}
                            onChange={handleChange}
                            onKeyDown={handleKeyDown}
                            onScroll={handleScroll}
                            placeholder="Enter SQL WHERE clause..."
                            spellCheck={false}
                        />
                    </div>
                    {showSuggestions && (
                        <div 
                            className="autocomplete-popup" 
                            style={{ top: cursorPosition.top, left: cursorPosition.left }}
                        >
                            {suggestions.map((s, i) => (
                                <div 
                                    key={s.text + i} 
                                    className={`suggestion-item ${i === suggestionIndex ? 'selected' : ''}`}
                                    onClick={() => applySuggestion(s)}
                                >
                                    <span>{s.text}</span>
                                    <span className="suggestion-type">{s.type}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                <div className="sql-editor-footer">
                    <button className="editor-button cancel" onClick={onClose}>Cancel</button>
                    <button className="editor-button save" onClick={() => onSave(value)}>Apply Filter</button>
                </div>
            </div>
        </div>
    );
}
