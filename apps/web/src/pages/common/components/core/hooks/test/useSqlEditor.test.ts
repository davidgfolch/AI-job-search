import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useSqlEditor } from '../useSqlEditor';
import * as ddlApi from '../../../../api/DdlApi';

vi.mock('../../../../api/DdlApi', () => ({
    fetchDdlSchema: vi.fn()
}));
vi.mock('../../../../utils/sqlEditorUtils', async () => {
    const actual = await vi.importActual('../../../../utils/sqlEditorUtils');
    return { ...actual, getCaretCoordinates: vi.fn().mockReturnValue({ top: 10, left: 10 }) };
});

describe('useSqlEditor', () => {
    const mockSchema = { tables: { users: ['id', 'name'], jobs: ['title'] }, keywords: ['SELECT', 'FROM'] };
    const textareaRef = { current: { value: '', selectionStart: 0, focus: vi.fn(), setSelectionRange: vi.fn() } as unknown as HTMLTextAreaElement };

    beforeEach(() => {
        vi.clearAllMocks();
        (ddlApi.fetchDdlSchema as any).mockResolvedValue(mockSchema);
    });

    const setupHook = (initialValue: string = '') => renderHook(() => useSqlEditor({ isOpen: true, initialValue, textareaRef }));

    it('should initialize and fetch schema', async () => {
        const { result } = setupHook('SELECT * FROM');
        expect(result.current.value).toBe('SELECT * FROM');
        await waitFor(() => expect(result.current.keywords).toEqual(mockSchema.keywords));
    });

    it.each([
        ['table', 'use', 3, 'users', 'table'],
        ['keyword', 'SEL', 3, 'SELECT', 'keyword'],
        ['column', 'users.na', 8, 'name', 'column']
    ])('should update suggestions for %s', async (_, input, cursor, expectedText, expectedType) => {
        const { result } = setupHook();
        await waitFor(() => expect(result.current.keywords).toEqual(mockSchema.keywords));
        // Update ref before specific operations if needed, though handleChange passes selectionStart from event
        // But for applySuggestion later we will need it on ref.
        act(() => result.current.handleChange({ target: { value: input, selectionStart: cursor } } as any));
        expect(result.current.showSuggestions).toBe(true);
        expect(result.current.suggestions).toEqual([{ text: expectedText, type: expectedType }]);
    });

    it('should apply suggestion', async () => {
        const { result } = setupHook();
        await waitFor(() => expect(result.current.keywords).toHaveLength(2));
        
        // Update ref state to match typing
        textareaRef.current.value = 'SEL';
        textareaRef.current.selectionStart = 3;
        
        act(() => result.current.handleChange({ target: { value: 'SEL', selectionStart: 3 } } as any));
        act(() => result.current.applySuggestion({ text: 'SELECT', type: 'keyword' }));
        expect(result.current.value).toBe('SELECT');
        expect(result.current.showSuggestions).toBe(false);
    });

    it('should navigate suggestions with keyboard', async () => {
        (ddlApi.fetchDdlSchema as any).mockResolvedValue({ ...mockSchema, keywords: ['SELECT', 'SET'] });
        const { result } = setupHook();
        await waitFor(() => expect(result.current.keywords).toHaveLength(2));
        
        // Update ref state
        textareaRef.current.value = 'S';
        textareaRef.current.selectionStart = 1;
        
        act(() => result.current.handleChange({ target: { value: 'S', selectionStart: 1 } } as any));
        
        const pressKey = (key: string) => act(() => result.current.handleKeyDown({ key, preventDefault: vi.fn() } as any));
        
        expect(result.current.suggestions.length).toBeGreaterThan(1);
        pressKey('ArrowDown');
        expect(result.current.suggestionIndex).toBe(1);
        pressKey('ArrowUp');
        expect(result.current.suggestionIndex).toBe(0);
        pressKey('ArrowUp'); // Loop to end
        expect(result.current.suggestionIndex).toBe(result.current.suggestions.length - 1);
        pressKey('Enter');
        expect(result.current.showSuggestions).toBe(false);
    });

    it('should close suggestions on Escape', async () => {
        const { result } = setupHook();
        await waitFor(() => expect(result.current.keywords).toHaveLength(2));
        act(() => result.current.handleChange({ target: { value: 'SEL', selectionStart: 3 } } as any));
        expect(result.current.showSuggestions).toBe(true);
        act(() => result.current.handleKeyDown({ key: 'Escape', preventDefault: vi.fn() } as any));
        expect(result.current.showSuggestions).toBe(false);
    });
});
