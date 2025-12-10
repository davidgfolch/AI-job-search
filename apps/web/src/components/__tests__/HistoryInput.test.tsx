// @vitest-environment jsdom
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import HistoryInput from '../HistoryInput';
import userEvent from '@testing-library/user-event';

describe('HistoryInput', () => {
    const defaultProps = {
        storageKey: 'test_history',
        value: '',
        onValueChange: vi.fn(),
    };


    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders input field', () => {
        render(<HistoryInput {...defaultProps} placeholder="Type here" />);
        expect(screen.getByPlaceholderText('Type here')).toBeInTheDocument();
    });

    it('loads history from localStorage', () => {
        localStorage.setItem('test_history', JSON.stringify(['previous value']));
        render(<HistoryInput {...defaultProps} />);

        const input = screen.getByRole('textbox');
        fireEvent.focus(input);

        expect(screen.getByText('previous value')).toBeInTheDocument();
    });

    it('saves to history on Enter', async () => {
        const user = userEvent.setup();
        render(<HistoryInput {...defaultProps} value="new value" />);

        const input = screen.getByRole('textbox');
        await user.type(input, '{Enter}');

        const stored = JSON.parse(localStorage.getItem('test_history') || '[]');
        expect(stored).toContain('new value');
    });

    it('shows suggestions on focus', async () => {
        localStorage.setItem('test_history', JSON.stringify(['item1', 'item2']));
        render(<HistoryInput {...defaultProps} />);

        const input = screen.getByRole('textbox');
        fireEvent.focus(input);

        expect(screen.getByText('item1')).toBeInTheDocument();
        expect(screen.getByText('item2')).toBeInTheDocument();
    });

    it('filters suggestions based on input', () => {
        localStorage.setItem('test_history', JSON.stringify(['apple', 'banana', 'apricot']));
        render(<HistoryInput {...defaultProps} value="ap" />);

        const input = screen.getByRole('textbox');
        fireEvent.focus(input);

        expect(screen.getByText('apple')).toBeInTheDocument();
        expect(screen.getByText('apricot')).toBeInTheDocument();
        expect(screen.queryByText('banana')).not.toBeInTheDocument();
    });

    it('selects suggestion on click', async () => {
        const onValueChange = vi.fn();
        localStorage.setItem('test_history', JSON.stringify(['clicked item']));
        render(<HistoryInput {...defaultProps} onValueChange={onValueChange} />);

        const input = screen.getByRole('textbox');
        fireEvent.focus(input);

        const suggestion = screen.getByText('clicked item');
        fireEvent.click(suggestion);

        expect(onValueChange).toHaveBeenCalledWith('clicked item');
    });
});
