import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import AppliedModal from '../AppliedModal';

// Mock IntersectionObserver for useAutoResizeTextArea
globalThis.IntersectionObserver = vi.fn(function(this: any) {
    return { observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() };
}) as any;

describe('AppliedModal', () => {
    const defaultProps = {
        isOpen: true,
        defaultComment: '- applied by 45k',
        onConfirm: vi.fn(),
        onCancel: vi.fn(),
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should not render when isOpen is false', () => {
        render(<AppliedModal {...defaultProps} isOpen={false} />);
        expect(screen.queryByText('Mark as Applied')).not.toBeInTheDocument();
    });

    it('should render modal when isOpen is true', () => {
        render(<AppliedModal {...defaultProps} />);
        expect(screen.getByText('Mark as Applied')).toBeInTheDocument();
        expect(screen.getByPlaceholderText('Enter comment...')).toBeInTheDocument();
        expect(screen.getByText('OK')).toBeInTheDocument();
        expect(screen.getByText("Don't set (Esc)")).toBeInTheDocument();
    });

    it('should display default comment in textarea', () => {
        render(<AppliedModal {...defaultProps} />);
        const textarea = screen.getByPlaceholderText('Enter comment...');
        expect(textarea).toHaveValue('- applied by 45k');
    });

    it('should call onConfirm with comment when OK button is clicked', () => {
        const mockConfirm = vi.fn();
        render(<AppliedModal {...defaultProps} onConfirm={mockConfirm} />);
        
        const okButton = screen.getByText('OK');
        fireEvent.click(okButton);
        
        expect(mockConfirm).toHaveBeenCalledWith(true, '- applied by 45k');
    });

    it('should call onConfirm without comment when "Don\'t set" button is clicked', () => {
        const mockConfirm = vi.fn();
        render(<AppliedModal {...defaultProps} onConfirm={mockConfirm} />);
        
        const dontSetButton = screen.getByText("Don't set (Esc)");
        fireEvent.click(dontSetButton);
        
        expect(mockConfirm).toHaveBeenCalledWith(false, '');
    });

    it('should call onConfirm with edited comment when user modifies text', () => {
        const mockConfirm = vi.fn();
        render(<AppliedModal {...defaultProps} onConfirm={mockConfirm} />);
        
        const textarea = screen.getByPlaceholderText('Enter comment...');
        fireEvent.change(textarea, { target: { value: '- applied with custom note' } });
        
        const okButton = screen.getByText('OK');
        fireEvent.click(okButton);
        
        expect(mockConfirm).toHaveBeenCalledWith(true, '- applied with custom note');
    });

    it('should call onCancel when overlay is clicked', () => {
        const mockOnCancel = vi.fn();
        render(<AppliedModal {...defaultProps} onCancel={mockOnCancel} />);
        
        const overlay = screen.getByText('Mark as Applied').closest('.modal-overlay');
        fireEvent.click(overlay!);
        
        expect(mockOnCancel).toHaveBeenCalled();
    });

    it('should confirm with Enter key', () => {
        const mockConfirm = vi.fn();
        render(<AppliedModal {...defaultProps} onConfirm={mockConfirm} />);
        
        fireEvent.keyDown(document, { key: 'Enter' });
        
        expect(mockConfirm).toHaveBeenCalledWith(true, '- applied by 45k');
    });

    it('should confirm without comment with Escape key', () => {
        const mockConfirm = vi.fn();
        render(<AppliedModal {...defaultProps} onConfirm={mockConfirm} />);
        
        fireEvent.keyDown(document, { key: 'Escape' });
        
        expect(mockConfirm).toHaveBeenCalledWith(false, '');
    });

    it('should not confirm with Enter key when Shift+Enter is pressed', () => {
        const mockConfirm = vi.fn();
        render(<AppliedModal {...defaultProps} onConfirm={mockConfirm} />);
        
        fireEvent.keyDown(document, { key: 'Enter', shiftKey: true });
        
        expect(mockConfirm).not.toHaveBeenCalled();
    });

    it('should focus textarea when modal opens', async () => {
        render(<AppliedModal {...defaultProps} />);
        
        // Wait for the focus to be applied (addressing timing issue)
        await act(async () => {
            await new Promise(resolve => setTimeout(resolve, 50));
        });
        
        const textarea = screen.getByPlaceholderText('Enter comment...');
        expect(textarea).toHaveFocus();
    });
});