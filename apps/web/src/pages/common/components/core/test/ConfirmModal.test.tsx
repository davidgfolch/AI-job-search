import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import ConfirmModal from '../../core/ConfirmModal';

describe('ConfirmModal', () => {
    const defaultProps = {
        isOpen: true,
        message: 'Are you sure?',
        onConfirm: vi.fn(),
        onCancel: vi.fn(),
    };

    afterEach(() => {
        vi.clearAllMocks();
    });

    it('should not render when isOpen is false', () => {
        const { container } = render(<ConfirmModal {...defaultProps} isOpen={false} />);
        expect(container).toBeEmptyDOMElement();
    });

    it('should render correctly when isOpen is true', () => {
        render(<ConfirmModal {...defaultProps} />);
        const confirmElements = screen.getAllByText('Confirm');
        expect(confirmElements.length).toBeGreaterThan(0); 
        expect(screen.getByText('Are you sure?')).toBeInTheDocument();
        expect(screen.getByText('Cancel')).toBeInTheDocument();
    });

    it('should render with a custom title', () => {
        render(<ConfirmModal {...defaultProps} title="Delete Item" />);
        expect(screen.getByText('Delete Item')).toBeInTheDocument();
    });

    it('should call onCancel when the Cancel button is clicked', () => {
        render(<ConfirmModal {...defaultProps} />);
        fireEvent.click(screen.getByText('Cancel'));
        expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
    });

    it('should call onConfirm when the Confirm button is clicked', () => {
        render(<ConfirmModal {...defaultProps} />);
        const button = screen.getByRole('button', { name: /confirm/i });
        fireEvent.click(button);
        expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
    });

    it('should call onCancel when clicking the overlay', () => {
        const { container } = render(<ConfirmModal {...defaultProps} />);
        // The overlay corresponds to the outer div
        const overlay = container.firstChild;
        if (overlay) {
            fireEvent.click(overlay);
            expect(defaultProps.onCancel).toHaveBeenCalledTimes(1);
        } else {
            throw new Error('Overlay not found');
        }
    });


    it('should not call onCancel when clicking inside the modal content', () => {
        render(<ConfirmModal {...defaultProps} />);
        const modalContent = screen.getByText('Are you sure?'); // Part of content
        fireEvent.click(modalContent);
        expect(defaultProps.onCancel).not.toHaveBeenCalled();
    });

    it('should call onConfirm when Ctrl+Enter is pressed', () => {
        render(<ConfirmModal {...defaultProps} />);
        fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true });
        expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
    });

    it('should call onConfirm when Meta+Enter is pressed', () => {
        render(<ConfirmModal {...defaultProps} />);
        fireEvent.keyDown(window, { key: 'Enter', metaKey: true });
        expect(defaultProps.onConfirm).toHaveBeenCalledTimes(1);
    });
});
