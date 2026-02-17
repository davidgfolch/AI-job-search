import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import HistoryInput from '../../core/HistoryInput';

describe('HistoryInput', () => {
    const defaultProps = {
        storageKey: 'test-history',
        value: '',
        onValueChange: vi.fn(),
        placeholder: 'Search...',
    };

    const testHistory = ["React", "Python", "Remote"];

    beforeEach(() => {
        localStorage.clear();
        vi.clearAllMocks();
    });

    // Helper to render and wait for initial async load
    const renderAndWait = async (props = defaultProps) => {
        const result = render(<HistoryInput {...props} />);
        // Wait for async effects - use vi.runAllTimers if needed, or just waitFor
        await waitFor(() => {}, { timeout: 100 });
        return result;
    };

    it('renders input with placeholder', async () => {
        await renderAndWait();
        expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
    });

    it('loads history from localStorage', async () => {
        localStorage.setItem('test-history', JSON.stringify(['react', 'vue']));
        render(<HistoryInput {...defaultProps} />);
        
        fireEvent.focus(screen.getByPlaceholderText('Search...'));
        
        expect(await screen.findByText('react')).toBeInTheDocument();
        expect(screen.getByText('vue')).toBeInTheDocument();
    });

    it('adds value to history on submit (Enter)', async () => {
        // Initialize with data to simulate previous default behavior
        localStorage.setItem('test-history', JSON.stringify(testHistory));
        const { rerender } = render(<HistoryInput {...defaultProps} value="" />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.focus(input);
        
        // Wait for defaults to load -> cleaner handling of the initial async effect
        await screen.findByText('React'); 
        
        // Now update to the test value
        rerender(<HistoryInput {...defaultProps} value="angular" />);
        
        // We need to re-query elements if they might have changed, though input ref is likely stable, safest to get again or use same if stable.
        // But fireEvent works on the element reference.
        
        // Trigger submit
        fireEvent.keyDown(input, { key: 'Enter' });

        // Wait for persistence to happen (it's async)
        await vi.waitUntil(() => {
             const stored = JSON.parse(localStorage.getItem('test-history') || '[]');
             return stored.includes('angular');
        });
    });

    it('adds value to history on blur if not empty', async () => {
        localStorage.setItem('test-history', JSON.stringify(testHistory));
        const { rerender } = render(<HistoryInput {...defaultProps} value="" />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.focus(input);
        await screen.findByText('React');

        rerender(<HistoryInput {...defaultProps} value="svelte" />);

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
        
        await screen.findByText('first');

        fireEvent.keyDown(input, { key: 'ArrowDown' });
        expect(screen.getByText('first')).toHaveClass('active');
        
        fireEvent.keyDown(input, { key: 'ArrowDown' });
        expect(screen.getByText('second')).toHaveClass('active');

        fireEvent.keyDown(input, { key: 'ArrowUp' });
        expect(screen.getByText('first')).toHaveClass('active');

        fireEvent.keyDown(input, { key: 'Enter' });
        expect(defaultProps.onValueChange).toHaveBeenCalledWith('first');
    });

    it('deletes item from history with keyboard', async () => {
        localStorage.setItem('test-history', JSON.stringify(['todelete', 'keep']));
        render(<HistoryInput {...defaultProps} />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.focus(input);
        
        await screen.findByText('todelete');

        fireEvent.keyDown(input, { key: 'ArrowDown' });
        
        fireEvent.keyDown(input, { key: 'Delete' });
        
        await vi.waitUntil(() => {
             const stored = JSON.parse(localStorage.getItem('test-history') || '[]');
             return !stored.includes('todelete') && stored.includes('keep');
        });

        expect(screen.queryByText('todelete')).not.toBeInTheDocument();
    });
});

