import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import JobEditForm from '../JobEditForm';
import { createMockJob, setupFakeTimers, cleanupFakeTimers } from '../../__tests__/test-utils';

const mockJob = createMockJob();

describe('JobEditForm Interactions', () => {
    let onUpdateMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        onUpdateMock = vi.fn();
        setupFakeTimers();
    });

    afterEach(() => {
        cleanupFakeTimers();
    });

    it('toggles status pill and calls onUpdate', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        const flaggedPill = screen.getByText('Flagged');
        fireEvent.click(flaggedPill);
        expect(onUpdateMock).toHaveBeenCalledWith({ flagged: true });
        expect(flaggedPill).toHaveClass('active');
    });

    it('updates status pill optimistically before API response', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        const likePill = screen.getByText('Like');
        expect(likePill).not.toHaveClass('active');
        fireEvent.click(likePill);
        // Should be active immediately (optimistic update)
        expect(likePill).toHaveClass('active');
        expect(onUpdateMock).toHaveBeenCalledWith({ like: true });
    });

    it('auto-saves comments after debounce delay', async () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        const commentsInput = screen.getByLabelText('Comments');
        fireEvent.change(commentsInput, { target: { value: 'New comment text' } });
        // Should not call onUpdate immediately
        expect(onUpdateMock).not.toHaveBeenCalled();
        // Fast-forward time by 1 second (debounce delay)
        vi.advanceTimersByTime(1000);
        // Now should have called onUpdate
        expect(onUpdateMock).toHaveBeenCalledWith({ comments: 'New comment text' });
    });

    it('auto-saves salary after debounce delay', async () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        const salaryInput = screen.getByLabelText('Salary');
        fireEvent.change(salaryInput, { target: { value: '120k' } });
        expect(onUpdateMock).not.toHaveBeenCalled();
        vi.advanceTimersByTime(1000);
        expect(onUpdateMock).toHaveBeenCalledWith({ salary: '120k' });
    });

    it('debounces multiple rapid changes correctly', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        const commentsInput = screen.getByLabelText('Comments');
        // Type rapidly
        fireEvent.change(commentsInput, { target: { value: 'First' } });
        vi.advanceTimersByTime(500);
        fireEvent.change(commentsInput, { target: { value: 'Second' } });
        vi.advanceTimersByTime(500);
        fireEvent.change(commentsInput, { target: { value: 'Third' } });
        // Should not have called yet
        expect(onUpdateMock).not.toHaveBeenCalled();
        // Complete the debounce
        vi.advanceTimersByTime(1000);
        // Should only save the final value once
        expect(onUpdateMock).toHaveBeenCalledTimes(1);
        expect(onUpdateMock).toHaveBeenCalledWith({ comments: 'Third' });
    });

    it('auto-resizes textarea based on content', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        const textarea = screen.getByLabelText('Comments') as HTMLTextAreaElement;
        // Mock scrollHeight to simulate content height changes
        Object.defineProperty(textarea, 'scrollHeight', {
            configurable: true,
            get: function () {
                return this.value.length > 50 ? 200 : 100;
            }
        });
        // Change to short content
        fireEvent.change(textarea, { target: { value: 'Short text' } });
        // Height should be set to 'auto' first, then to scrollHeight
        expect(textarea.style.height).toBe('100px');
        // Change to longer content
        const longText = 'This is a much longer comment that would require more vertical space to display properly';
        fireEvent.change(textarea, { target: { value: longText } });
        expect(textarea.style.height).toBe('200px');
    });
});
