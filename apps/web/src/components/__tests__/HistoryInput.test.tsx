import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import HistoryInput from '../HistoryInput';

describe('HistoryInput', () => {
    const defaultProps = {
        storageKey: 'test-history',
        value: '',
        onValueChange: vi.fn(),
        placeholder: 'Search...',
    };

    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
    });

    it('renders input with placeholder', () => {
        render(<HistoryInput {...defaultProps} />);
        expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
    });

    it('loads history from localStorage', async () => {
        localStorage.setItem('test-history', JSON.stringify(['react', 'vue']));
        render(<HistoryInput {...defaultProps} />);
        
        // Focus to show suggestions
        fireEvent.focus(screen.getByPlaceholderText('Search...'));
        
        // Wait for async load
        expect(await screen.findByText('react')).toBeInTheDocument();
        expect(screen.getByText('vue')).toBeInTheDocument();
    });

    it('adds value to history on submit (Enter)', async () => {
        render(<HistoryInput {...defaultProps} value="angular" />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.keyDown(input, { key: 'Enter' });

        // Wait for persistence to happen (it's async)
        // We can check localStorage but might need a small wait if the implementation doesn't await the setItem in the effect or handler
        // The implementation does `await persistenceApi.setValue` but it's fire-and-forget from the handler's perspective (handler is sync)
        
        // Wait for the value to appear in local storage
        await vi.waitUntil(() => {
             const stored = JSON.parse(localStorage.getItem('test-history') || '[]');
             return stored.includes('angular');
        });
    });

    it('adds value to history on blur if not empty', async () => {
        render(<HistoryInput {...defaultProps} value="svelte" />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.blur(input);

        await vi.waitUntil(() => {
            const stored = JSON.parse(localStorage.getItem('test-history') || '[]');
            return stored.includes('svelte');
       });
    });

    it('filters history based on input', async () => {
        localStorage.setItem('test-history', JSON.stringify(['react', 'redux', 'vue']));
        render(<HistoryInput {...defaultProps} value="re" />);
        
        fireEvent.focus(screen.getByPlaceholderText('Search...'));

        // Wait for loading
        expect(await screen.findByText('react')).toBeInTheDocument();
        expect(screen.getByText('redux')).toBeInTheDocument();
        expect(screen.queryByText('vue')).not.toBeInTheDocument();
    });

    it('selects item from history on click', async () => {
        localStorage.setItem('test-history', JSON.stringify(['react']));
        render(<HistoryInput {...defaultProps} />);
        
        fireEvent.focus(screen.getByPlaceholderText('Search...'));
        
        const item = await screen.findByText('react');
        fireEvent.click(item);

        expect(defaultProps.onValueChange).toHaveBeenCalledWith('react');
    });

    it('navigates history with keyboard', async () => {
        localStorage.setItem('test-history', JSON.stringify(['first', 'second']));
        render(<HistoryInput {...defaultProps} />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.focus(input);
        
        // Wait for items to load
        await screen.findByText('first');

        // Arrow Down -> highlight first
        fireEvent.keyDown(input, { key: 'ArrowDown' });
        expect(screen.getByText('first')).toHaveClass('active');
        
        // Arrow Down -> highlight second
        fireEvent.keyDown(input, { key: 'ArrowDown' });
        expect(screen.getByText('second')).toHaveClass('active');

        // Arrow Up -> highlight first
        fireEvent.keyDown(input, { key: 'ArrowUp' });
        expect(screen.getByText('first')).toHaveClass('active');

        // Enter -> select first
        fireEvent.keyDown(input, { key: 'Enter' });
        expect(defaultProps.onValueChange).toHaveBeenCalledWith('first');
    });

    it('deletes item from history with keyboard', async () => {
        localStorage.setItem('test-history', JSON.stringify(['todelete', 'keep']));
        render(<HistoryInput {...defaultProps} />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.focus(input);
        
        // Wait for items
        await screen.findByText('todelete');

        // Highlight first
        fireEvent.keyDown(input, { key: 'ArrowDown' });
        
        // Delete
        fireEvent.keyDown(input, { key: 'Delete' });
        
        // Wait for removal from storage
        await vi.waitUntil(() => {
             const stored = JSON.parse(localStorage.getItem('test-history') || '[]');
             return !stored.includes('todelete') && stored.includes('keep');
        });

        // UI update check (it filters based on state, state updates optimistically)
        expect(screen.queryByText('todelete')).not.toBeInTheDocument();
    });
});
