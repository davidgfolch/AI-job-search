import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import JobEditForm from '../JobEditForm';
import { createMockJob, setupFakeTimers, cleanupFakeTimers } from '../../__tests__/test-utils';

const mockJob = createMockJob();

describe('JobEditForm', () => {
    let onUpdateMock: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        onUpdateMock = vi.fn();
        setupFakeTimers();
    });

    afterEach(() => {
        cleanupFakeTimers();
    });

    it('renders "Select a job to edit" when no job is selected', () => {
        render(<JobEditForm job={null} onUpdate={onUpdateMock} />);
        expect(screen.getByText('Select a job to edit')).toBeInTheDocument();
    });

    it('renders form with job data when job is selected', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        expect(screen.getByLabelText('Comments')).toHaveValue('Test comment');
        expect(screen.getByLabelText('Salary')).toHaveValue('100k');
        expect(screen.getByLabelText('Client')).toHaveValue('Client A');
    });

    it('displays all status pills', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        const statusFields = [
            'Flagged', 'Like', 'Ignored', 'Seen', 'Applied', 'Discarded', 'Closed',
            'Interview (RH)', 'Interview', 'Interview (Tech)', 'Technical Test', 'Technical Test Done',
            'AI Enriched', 'Easy Apply'
        ];
        statusFields.forEach(field => {
            expect(screen.getByText(field)).toBeInTheDocument();
        });
    });

    it('shows active state for true status fields', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        const aiEnrichedPill = screen.getByText('AI Enriched');
        expect(aiEnrichedPill).toHaveClass('active');
        const flaggedPill = screen.getByText('Flagged');
        expect(flaggedPill).not.toHaveClass('active');
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

    it('syncs form fields when job prop changes', () => {
        const { rerender } = render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        expect(screen.getByLabelText('Comments')).toHaveValue('Test comment');
        const updatedJob = { ...mockJob, comments: 'Updated from outside' };
        rerender(<JobEditForm job={updatedJob} onUpdate={onUpdateMock} />);
        expect(screen.getByLabelText('Comments')).toHaveValue('Updated from outside');
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

    it('toggles status pill in create mode (local state only)', () => {
        render(<JobEditForm job={null} onUpdate={onUpdateMock} mode="create" />);
        const flaggedPill = screen.getByText('Flagged');
        // Initial click - sets to true locally
        fireEvent.click(flaggedPill);
        expect(flaggedPill).toHaveClass('active');
        expect(onUpdateMock).not.toHaveBeenCalled(); // Should not call onUpdate in create mode
        // Second click - sets to false locally
        fireEvent.click(flaggedPill);
        expect(flaggedPill).not.toHaveClass('active');
    });

    it('calls onCreate when Create Job button is clicked', () => {
        const onCreateMock = vi.fn();
        render(<JobEditForm job={null} onUpdate={onUpdateMock} onCreate={onCreateMock} mode="create" />);
        const titleInput = screen.getByLabelText('Title *');
        const companyInput = screen.getByLabelText('Company *');
        fireEvent.change(titleInput, { target: { value: 'New Job Title' } });
        fireEvent.change(companyInput, { target: { value: 'New Company' } });
        // Toggle a status to ensure it's included in creation
        const flaggedPill = screen.getByText('Flagged');
        fireEvent.click(flaggedPill);
        const createButton = screen.getByText('Create Job');
        expect(createButton).not.toBeDisabled();
        fireEvent.click(createButton);
        expect(onCreateMock).toHaveBeenCalledWith(expect.objectContaining({
            title: 'New Job Title',
            company: 'New Company',
            flagged: true
        }));
    });

});
