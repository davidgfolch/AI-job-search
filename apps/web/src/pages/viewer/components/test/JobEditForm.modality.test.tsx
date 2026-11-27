import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';
import JobEditForm from "../JobEditForm";
import type { Job } from '../../api/ViewerApi';
import { createMockJob, setupFakeTimers, cleanupFakeTimers } from '../../test/test-utils';

vi.mock('../../../common/hooks/useModalityValues', () => ({
    useModalityValues: vi.fn().mockReturnValue({ data: ['REMOTE', 'HYBRID', 'ON_SITE'] }),
}));

const mockJob = createMockJob();

describe('JobEditForm modality and hybrid info', () => {
    let onUpdateMock: Mock<(data: Partial<Job>) => void>;

    beforeEach(() => {
        const MockObserver = class {
            observe = vi.fn();
            unobserve = vi.fn();
            disconnect = vi.fn();
        };
        window.IntersectionObserver = MockObserver as unknown as typeof IntersectionObserver;
        globalThis.IntersectionObserver = MockObserver as unknown as typeof IntersectionObserver;

        onUpdateMock = vi.fn();
        setupFakeTimers();
    });

    afterEach(() => {
        cleanupFakeTimers();
    });

    it('adds a modality value', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        fireEvent.click(screen.getByText('Edit All'));

        expect(screen.getByLabelText('Modality')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'REMOTE' }));

        expect(onUpdateMock).toHaveBeenCalledWith({ modality: ['REMOTE'] });
    });

    it('keeps every selected modality and clears to null', () => {
        render(<JobEditForm job={{ ...mockJob, modality: ['REMOTE'] }} onUpdate={onUpdateMock} />);
        fireEvent.click(screen.getByText('Edit All'));

        fireEvent.click(screen.getByRole('button', { name: 'HYBRID' }));
        expect(onUpdateMock).toHaveBeenLastCalledWith({ modality: ['REMOTE', 'HYBRID'] });

        fireEvent.click(screen.getByRole('button', { name: 'REMOTE' }));
        fireEvent.click(screen.getByRole('button', { name: 'HYBRID' }));
        expect(onUpdateMock).toHaveBeenLastCalledWith({ modality: null });
    });

    it('renders hybrid info when editing all fields', () => {
        render(<JobEditForm job={{ ...mockJob, hybrid_info: '3 days remote / 2 days office' }} onUpdate={onUpdateMock} />);
        expect(screen.queryByLabelText('Hybrid info')).not.toBeInTheDocument();

        fireEvent.click(screen.getByText('Edit All'));
        expect(screen.getByLabelText('Hybrid info')).toHaveValue('3 days remote / 2 days office');
    });

    it('autosaves hybrid info after the debounce', () => {
        render(<JobEditForm job={mockJob} onUpdate={onUpdateMock} />);
        fireEvent.click(screen.getByText('Edit All'));

        fireEvent.change(screen.getByLabelText('Hybrid info'), { target: { value: '2 days office' } });
        expect(onUpdateMock).not.toHaveBeenCalled();

        act(() => { vi.advanceTimersByTime(1000); });
        expect(onUpdateMock).toHaveBeenCalledWith({ hybrid_info: '2 days office' });
    });

    it('includes modality in create payload', () => {
        const onCreateMock = vi.fn();
        render(<JobEditForm job={null} onUpdate={onUpdateMock} onCreate={onCreateMock} mode="create" />);

        const titleInput = screen.getByLabelText('Title *');
        const companyInput = screen.getByLabelText('Company *');
        fireEvent.change(titleInput, { target: { value: 'New Job Title' } });
        fireEvent.change(companyInput, { target: { value: 'New Company' } });

        fireEvent.click(screen.getByRole('button', { name: 'HYBRID' }));

        const createButton = screen.getByRole('button', { name: /Create Job/i });
        fireEvent.click(createButton);

        expect(onCreateMock).toHaveBeenCalled();
        expect(onCreateMock).toHaveBeenCalledWith(expect.objectContaining({
            title: 'New Job Title',
            company: 'New Company',
            modality: ['HYBRID'],
        }));
    });

    it('includes hybrid info in create payload', () => {
        const onCreateMock = vi.fn();
        render(<JobEditForm job={null} onUpdate={onUpdateMock} onCreate={onCreateMock} mode="create" />);

        fireEvent.change(screen.getByLabelText('Title *'), { target: { value: 'New Job Title' } });
        fireEvent.change(screen.getByLabelText('Company *'), { target: { value: 'New Company' } });
        fireEvent.change(screen.getByLabelText('Hybrid info'), { target: { value: '3 days remote / 2 days office' } });

        fireEvent.click(screen.getByRole('button', { name: /Create Job/i }));

        expect(onCreateMock).toHaveBeenCalledWith(expect.objectContaining({
            title: 'New Job Title',
            company: 'New Company',
            hybrid_info: '3 days remote / 2 days office',
        }));
    });
});
