import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import JobEditForm from "../JobEditForm";
import { createMockJobs, createMockJob, setupFakeTimers, cleanupFakeTimers } from '../../test/test-utils';

const mockJob = createMockJob();

describe('JobEditForm', () => {
    let onUpdateMock: any;

    beforeEach(() => {
        const MockObserver = class {
            observe = vi.fn();
            unobserve = vi.fn();
            disconnect = vi.fn();
        };
        window.IntersectionObserver = MockObserver as any;
        globalThis.IntersectionObserver = MockObserver as any;
        
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



    it('syncs form fields when job prop changes', () => {
        const { rerender } = render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        expect(screen.getByLabelText('Comments')).toHaveValue('Test comment');
        const updatedJob = { ...mockJob, comments: 'Updated from outside' };
        rerender(<JobEditForm job={updatedJob} onUpdate={onUpdateMock} />);
        expect(screen.getByLabelText('Comments')).toHaveValue('Updated from outside');
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

    it('renders simplified view by default in edit mode', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        
        // Always visible fields
        expect(screen.getByLabelText('Comments')).toBeInTheDocument();
        expect(screen.getByLabelText('Salary')).toBeInTheDocument();
        expect(screen.getByLabelText('Client')).toBeInTheDocument();
        
        // Hidden fields
        expect(screen.queryByLabelText('Title *')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('Company *')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('Location')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('Description')).not.toBeInTheDocument();
        
        // Toggle button exists
        expect(screen.getByText('Edit All')).toBeInTheDocument();
    });

    it('toggles hidden fields when button is clicked', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        
        const toggleBtn = screen.getByText('Edit All');
        
        // Expand
        fireEvent.click(toggleBtn);
        
        expect(screen.getByLabelText('Location')).toBeInTheDocument();
        expect(screen.getByLabelText('Description')).toBeInTheDocument();
        expect(screen.getByLabelText('Title *')).toBeInTheDocument();
        
        // Button text should change
        expect(screen.getByText('Edit Less')).toBeInTheDocument();
        
        // Collapse
        fireEvent.click(toggleBtn);
        
        expect(screen.queryByLabelText('Location')).not.toBeInTheDocument();
        expect(screen.queryByLabelText('Description')).not.toBeInTheDocument();
        expect(screen.getByText('Edit All')).toBeInTheDocument();
    });

    it('applies hide-labels class in create mode or when showing all fields', () => {
        const { rerender, container } = render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} mode="create" />);
        // Create mode -> hide-labels should be present
        expect(container.querySelector('.form-fields')).toHaveClass('hide-labels');

        rerender(<JobEditForm job={mockJob} onUpdate={onUpdateMock} mode="edit" />);
        // Edit mode (default) -> hide-labels should NOT be present
        expect(container.querySelector('.form-fields')).not.toHaveClass('hide-labels');

        // Toggle Edit All
        fireEvent.click(screen.getByText('Edit All'));
        expect(container.querySelector('.form-fields')).toHaveClass('hide-labels');
    });

    it('remains in "Edit All" mode when job data updates', () => {
        const { rerender } = render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        
        // Switch to "Edit All" mode
        const toggleBtn = screen.getByText('Edit All');
        fireEvent.click(toggleBtn);
        expect(screen.getByText('Edit Less')).toBeInTheDocument();

        // Simulate job update from parent (e.g. after optimistic update)
        const updatedJob = { ...mockJob, comments: 'New comment' };
        rerender(<JobEditForm job={updatedJob} onUpdate={onUpdateMock} />);

        // Should still be in "Edit All" mode
        expect(screen.queryByText('Edit Less')).toBeInTheDocument();
        expect(screen.queryByText('Edit All')).not.toBeInTheDocument();
    });
});
