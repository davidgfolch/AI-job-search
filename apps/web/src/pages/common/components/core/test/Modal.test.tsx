import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { Modal } from '../../core/Modal';

describe('Modal', () => {
    const defaultProps = {
        isOpen: true,
        onClose: vi.fn(),
        children: <div>Modal content</div>,
    };

    afterEach(() => {
        vi.clearAllMocks();
    });

    it('should not render when isOpen is false', () => {
        const { container } = render(<Modal {...defaultProps} isOpen={false} />);
        expect(container).toBeEmptyDOMElement();
    });

    it('should render children when isOpen is true', () => {
        render(<Modal {...defaultProps} />);
        expect(screen.getByText('Modal content')).toBeInTheDocument();
    });

    it('should render with title when provided', () => {
        render(<Modal {...defaultProps} title="Test Title" />);
        expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    it('should render with custom header when provided', () => {
        render(<Modal {...defaultProps} header={<div data-testid="custom-header">Custom Header</div>} />);
        expect(screen.getByTestId('custom-header')).toBeInTheDocument();
    });

    it('should render footer when provided', () => {
        render(<Modal {...defaultProps} footer={<button>Action</button>} />);
        expect(screen.getByText('Action')).toBeInTheDocument();
    });

    it('should call onClose when clicking the overlay', () => {
        const { container } = render(<Modal {...defaultProps} />);
        const overlay = container.firstChild;
        if (overlay) {
            fireEvent.click(overlay);
            expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
        } else {
            throw new Error('Overlay not found');
        }
    });

    it('should not call onClose when clicking inside the modal content', () => {
        render(<Modal {...defaultProps} />);
        const modalContent = screen.getByText('Modal content');
        fireEvent.click(modalContent);
        expect(defaultProps.onClose).not.toHaveBeenCalled();
    });

    it('should call onClose when Escape is pressed', () => {
        render(<Modal {...defaultProps} closeOnEscape />);
        fireEvent.keyDown(window, { key: 'Escape' });
        expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    });

    it('should not call onClose when Escape is pressed and closeOnEscape is false', () => {
        render(<Modal {...defaultProps} closeOnEscape={false} />);
        fireEvent.keyDown(window, { key: 'Escape' });
        expect(defaultProps.onClose).not.toHaveBeenCalled();
    });

    it('should not call onClose when clicking overlay and closeOnOverlayClick is false', () => {
        const { container } = render(<Modal {...defaultProps} closeOnOverlayClick={false} />);
        const overlay = container.firstChild;
        if (overlay) {
            fireEvent.click(overlay);
            expect(defaultProps.onClose).not.toHaveBeenCalled();
        } else {
            throw new Error('Overlay not found');
        }
    });

    it('should apply custom className', () => {
        const { container } = render(<Modal {...defaultProps} className="custom-class" />);
        const content = container.querySelector('.modal-content');
        expect(content).toHaveClass('custom-class');
    });
});
