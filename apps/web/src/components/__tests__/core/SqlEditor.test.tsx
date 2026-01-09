import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SqlEditor from '../../core/SqlEditor';
import * as useSqlEditorHook from '../../../hooks/useSqlEditor';

// Mock the hook
vi.mock('../../../hooks/useSqlEditor', () => ({
    useSqlEditor: vi.fn()
}));

// Mock scrollIntoView for suggestion items if needed (jsdom doesn't implement it)
window.HTMLElement.prototype.scrollIntoView = vi.fn();

describe('SqlEditor', () => {
    const defaultHookValues = {
        value: 'SELECT * FROM users',
        suggestions: [],
        schema: {},
        keywords: [],
        showSuggestions: false,
        suggestionIndex: 0,
        cursorPosition: { top: 0, left: 0 },
        handleChange: vi.fn(),
        handleKeyDown: vi.fn(),
        applySuggestion: vi.fn()
    };

    beforeEach(() => {
        vi.clearAllMocks();
        (useSqlEditorHook.useSqlEditor as any).mockReturnValue(defaultHookValues);
    });

    it('should not render when isOpen is false', () => {
        render(
            <SqlEditor 
                isOpen={false} 
                initialValue="" 
                onSave={vi.fn()} 
                onClose={vi.fn()} 
            />
        );
        expect(screen.queryByText('SQL Editor')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
        render(
            <SqlEditor 
                isOpen={true} 
                initialValue="SELECT" 
                onSave={vi.fn()} 
                onClose={vi.fn()} 
            />
        );
        expect(screen.getByText('SQL Editor')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Enter SQL WHERE clause...')).toBeInTheDocument();
        expect(screen.getByDisplayValue('SELECT * FROM users')).toBeInTheDocument(); // value comes from hook mock
    });

    it('should call onClose when cancel button is clicked', () => {
        const onCloseMock = vi.fn();
        render(
            <SqlEditor 
                isOpen={true} 
                initialValue="" 
                onSave={vi.fn()} 
                onClose={onCloseMock} 
            />
        );
        
        const closeButtons = screen.getAllByText((content, element) => {
            return element?.tagName.toLowerCase() === 'button' && (content === '✕' || content === 'Cancel');
        });
        
        fireEvent.click(closeButtons[0]); // Test the X button
        expect(onCloseMock).toHaveBeenCalledTimes(1);
    });

    it('should call onSave with current value when Apply Filter is clicked', () => {
        const onSaveMock = vi.fn();
        render(
            <SqlEditor 
                isOpen={true} 
                initialValue="" 
                onSave={onSaveMock} 
                onClose={vi.fn()} 
            />
        );
        
        fireEvent.click(screen.getByText('Apply Filter'));
        expect(onSaveMock).toHaveBeenCalledWith('SELECT * FROM users');
    });

    it('should render suggestions when showSuggestions is true', () => {
        (useSqlEditorHook.useSqlEditor as any).mockReturnValue({
            ...defaultHookValues,
            showSuggestions: true,
            suggestions: [
                { text: 'users', type: 'table' },
                { text: 'WHERE', type: 'keyword' }
            ]
        });

        const { container } = render(
            <SqlEditor 
                isOpen={true} 
                initialValue="" 
                onSave={vi.fn()} 
                onClose={vi.fn()} 
            />
        );
        
        // Scope to autocomplete popup
        const popup = container.querySelector('.autocomplete-popup');
        expect(popup).toBeInTheDocument();
        // Use within or simple text match inside popup
        expect(screen.getAllByText('users').length).toBeGreaterThanOrEqual(1); // One in editor (highlight), one in suggestion
        // Better:
        expect(popup).toHaveTextContent('users');
        expect(popup).toHaveTextContent('WHERE');
    });

    it('should call applySuggestion when a suggestion is clicked', () => {
        const applySuggestionMock = vi.fn();
        const suggestions = [{ text: 'users', type: 'table' as const }];
        
        (useSqlEditorHook.useSqlEditor as any).mockReturnValue({
            ...defaultHookValues,
            showSuggestions: true,
            suggestions,
            applySuggestion: applySuggestionMock
        });

        const { container } = render(
            <SqlEditor 
                isOpen={true} 
                initialValue="" 
                onSave={vi.fn()} 
                onClose={vi.fn()} 
            />
        );
        
        const popup = container.querySelector('.autocomplete-popup');
        const userSuggestion = screen.getAllByText('users').find(el => popup?.contains(el));
        
        if (!userSuggestion) throw new Error('Suggestion not found in popup');

        fireEvent.click(userSuggestion);
        expect(applySuggestionMock).toHaveBeenCalledWith(suggestions[0]);
    });

    it('should trigger handleChange when typing', () => {
        const handleChangeMock = vi.fn();
        (useSqlEditorHook.useSqlEditor as any).mockReturnValue({
            ...defaultHookValues,
            handleChange: handleChangeMock
        });

        render(
            <SqlEditor 
                isOpen={true} 
                initialValue="" 
                onSave={vi.fn()} 
                onClose={vi.fn()} 
            />
        );
        
        fireEvent.change(screen.getByRole('textbox'), { target: { value: 'New Value' } });
        expect(handleChangeMock).toHaveBeenCalled();
    });
});
