import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import JobEditForm from "../JobEditForm";
import { createMockJob, setupFakeTimers, cleanupFakeTimers } from '../../test/test-utils';

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

    it.each([
        ['Comments', 'Test comment'],
        ['Salary', '100k'],
        ['Client', 'Client A']
    ])('renders form field %s with correct value', (label, expectedValue) => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        expect(screen.getByLabelText(label)).toHaveValue(expectedValue);
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
        expect(screen.getByText('AI Enriched')).toHaveClass('active');
        expect(screen.getByText('Flagged')).not.toHaveClass('active');
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
        
        fireEvent.click(flaggedPill);
        expect(flaggedPill).toHaveClass('active');
        expect(onUpdateMock).not.toHaveBeenCalled(); 
        
        fireEvent.click(flaggedPill);
        expect(flaggedPill).not.toHaveClass('active');
    });

    it('calls onCreate when Create Job button is clicked', () => {
        const onCreateMock = vi.fn();
        render(<JobEditForm job={null} onUpdate={onUpdateMock} onCreate={onCreateMock} mode="create" />);
        
        fireEvent.change(screen.getByLabelText('Title *'), { target: { value: 'New Job Title' } });
        fireEvent.change(screen.getByLabelText('Company *'), { target: { value: 'New Company' } });
        fireEvent.click(screen.getByText('Flagged'));
        
        const createButton = screen.getByText('Create Job');
        expect(createButton).not.toBeDisabled();
        fireEvent.click(createButton);
        
        expect(onCreateMock).toHaveBeenCalledWith(expect.objectContaining({
            title: 'New Job Title',
            company: 'New Company',
            flagged: true
        }));
    });

    it('toggles visibility of advanced fields', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        const toggleBtn = screen.getByText('Edit All');
        
        // Initial state
        expect(screen.queryByLabelText('Title *')).not.toBeInTheDocument();
        
        // Expand
        fireEvent.click(toggleBtn);
        expect(screen.getByLabelText('Title *')).toBeInTheDocument();
        expect(screen.getByText('Edit Less')).toBeInTheDocument();
        
        // Collapse
        fireEvent.click(toggleBtn);
        expect(screen.queryByLabelText('Title *')).not.toBeInTheDocument();
    });

    it('remains in "Edit All" mode when job data updates', () => {
        const { rerender } = render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        fireEvent.click(screen.getByText('Edit All'));
        expect(screen.getByText('Edit Less')).toBeInTheDocument();

        rerender(<JobEditForm job={{ ...mockJob, comments: 'New comment' }} onUpdate={onUpdateMock} />);
        expect(screen.queryByText('Edit Less')).toBeInTheDocument();
    });

    it.each([
        ['Required Skills', 'required_technologies'],
        ['Optional Skills', 'optional_technologies']
    ])('updates %s field correctly', (label, fieldKey) => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        
        fireEvent.click(screen.getByText('Edit All'));

        const input = screen.getByLabelText(label);
        expect(input).toBeInTheDocument();

        fireEvent.change(input, { target: { value: 'New, Skills' } });
        vi.runAllTimers();
        
        expect(onUpdateMock).toHaveBeenCalledWith({ [fieldKey]: 'New, Skills' });
    });
});
