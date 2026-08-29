import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { EditSynonymGroupModal } from '../EditSynonymGroupModal';

describe('EditSynonymGroupModal', () => {
    const defaultProps = { onSave: vi.fn(), onClose: vi.fn() };

    afterEach(() => {
        vi.clearAllMocks();
    });

    it('renders with two empty company name inputs', () => {
        render(<EditSynonymGroupModal {...defaultProps} />);
        expect(screen.getAllByPlaceholderText(/Company name/)).toHaveLength(2);
        expect(screen.getByRole('button', { name: /Save/i })).toBeDisabled();
    });

    it('shows New Synonym Group heading when creating', () => {
        render(<EditSynonymGroupModal {...defaultProps} />);
        expect(screen.getByText('New Synonym Group')).toBeInTheDocument();
    });

    it('enables Save when at least two names are filled', () => {
        render(<EditSynonymGroupModal {...defaultProps} />);
        const inputs = screen.getAllByPlaceholderText(/Company name/);
        fireEvent.change(inputs[0], { target: { value: 'Acme' } });
        fireEvent.change(inputs[1], { target: { value: 'Acme Inc' } });
        expect(screen.getByRole('button', { name: /Save/i })).toBeEnabled();
    });

    it('saves trimmed names when Save is clicked', () => {
        render(<EditSynonymGroupModal {...defaultProps} />);
        const inputs = screen.getAllByPlaceholderText(/Company name/);
        fireEvent.change(inputs[0], { target: { value: '  Acme  ' } });
        fireEvent.change(inputs[1], { target: { value: 'Acme Inc' } });
        fireEvent.click(screen.getByRole('button', { name: /Save/i }));
        expect(defaultProps.onSave).toHaveBeenCalledWith(['Acme', 'Acme Inc']);
    });

    it('calls onSave when Enter is pressed with valid names', () => {
        render(<EditSynonymGroupModal {...defaultProps} />);
        const inputs = screen.getAllByPlaceholderText(/Company name/);
        fireEvent.change(inputs[0], { target: { value: 'Acme' } });
        fireEvent.change(inputs[1], { target: { value: 'Acme Inc' } });
        fireEvent.keyDown(window, { key: 'Enter' });
        expect(defaultProps.onSave).toHaveBeenCalledTimes(1);
    });

    it('does not call onSave when Enter is pressed with invalid names', () => {
        render(<EditSynonymGroupModal {...defaultProps} />);
        const inputs = screen.getAllByPlaceholderText(/Company name/);
        fireEvent.change(inputs[0], { target: { value: 'Acme' } });
        fireEvent.keyDown(window, { key: 'Enter' });
        expect(defaultProps.onSave).not.toHaveBeenCalled();
    });

    it('calls onClose when Cancel is clicked', () => {
        render(<EditSynonymGroupModal {...defaultProps} />);
        fireEvent.click(screen.getByRole('button', { name: /Cancel/i }));
        expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when Escape is pressed', () => {
        render(<EditSynonymGroupModal {...defaultProps} />);
        fireEvent.keyDown(window, { key: 'Escape' });
        expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('adds and removes synonym rows', () => {
        render(<EditSynonymGroupModal {...defaultProps} />);
        fireEvent.click(screen.getByRole('button', { name: /Add another/i }));
        expect(screen.getAllByPlaceholderText(/Company name/)).toHaveLength(3);
        fireEvent.click(screen.getAllByText('×')[0]);
        expect(screen.getAllByPlaceholderText(/Company name/)).toHaveLength(2);
    });
});
