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

    it('loads history from localStorage', () => {
        localStorage.setItem('test-history', JSON.stringify(['react', 'vue']));
        render(<HistoryInput {...defaultProps} />);
        
        // Focus to show suggestions
        fireEvent.focus(screen.getByPlaceholderText('Search...'));
        
        expect(screen.getByText('react')).toBeInTheDocument();
        expect(screen.getByText('vue')).toBeInTheDocument();
    });

    it('adds value to history on submit (Enter)', () => {
        render(<HistoryInput {...defaultProps} value="angular" />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.keyDown(input, { key: 'Enter' });

        const stored = JSON.parse(localStorage.getItem('test-history') || '[]');
        expect(stored).toContain('angular');
    });

    it('adds value to history on blur if not empty', () => {
        render(<HistoryInput {...defaultProps} value="svelte" />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.blur(input);

        const stored = JSON.parse(localStorage.getItem('test-history') || '[]');
        expect(stored).toContain('svelte');
    });

    it('filters history based on input', () => {
        localStorage.setItem('test-history', JSON.stringify(['react', 'redux', 'vue']));
        render(<HistoryInput {...defaultProps} value="re" />);
        
        fireEvent.focus(screen.getByPlaceholderText('Search...'));

        expect(screen.getByText('react')).toBeInTheDocument();
        expect(screen.getByText('redux')).toBeInTheDocument();
        expect(screen.queryByText('vue')).not.toBeInTheDocument();
    });

    it('selects item from history on click', () => {
        localStorage.setItem('test-history', JSON.stringify(['react']));
        render(<HistoryInput {...defaultProps} />);
        
        fireEvent.focus(screen.getByPlaceholderText('Search...'));
        fireEvent.click(screen.getByText('react'));

        expect(defaultProps.onValueChange).toHaveBeenCalledWith('react');
    });

    it('navigates history with keyboard', () => {
        localStorage.setItem('test-history', JSON.stringify(['first', 'second']));
        render(<HistoryInput {...defaultProps} />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.focus(input);
        
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

    it('deletes item from history with keyboard', () => {
        localStorage.setItem('test-history', JSON.stringify(['todelete', 'keep']));
        render(<HistoryInput {...defaultProps} />);
        
        const input = screen.getByPlaceholderText('Search...');
        fireEvent.focus(input);
        
        // Highlight first
        fireEvent.keyDown(input, { key: 'ArrowDown' });
        
        // Delete
        fireEvent.keyDown(input, { key: 'Delete' });
        
        const stored = JSON.parse(localStorage.getItem('test-history') || '[]');
        expect(stored).not.toContain('todelete');
        expect(stored).toContain('keep');
        expect(screen.queryByText('todelete')).not.toBeInTheDocument();
    });
});
