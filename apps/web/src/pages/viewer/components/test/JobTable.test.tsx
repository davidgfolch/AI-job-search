import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import JobTable from "../JobTable";
import { createMockJobs } from "../../test/test-utils";
import { createRef } from 'react';

const mockJobs = createMockJobs(2, {
    required_technologies: 'React',
    optional_technologies: 'Python',
});

describe('JobTable', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        Element.prototype.scrollIntoView = vi.fn();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

const defaultProps = {
        jobs: mockJobs,
        selectedJob: null,
        onJobSelect: vi.fn(),
        selectedIds: new Set<number>(),
        selectionMode: 'none' as const,
        onToggleSelectJob: vi.fn(),
        onToggleSelectAll: vi.fn(),
        containerRef: createRef<HTMLDivElement>(),
    };

    it('renders job list correctly', () => {
        render(<JobTable {...defaultProps} />);

        expect(screen.getByText('Job 1')).toBeInTheDocument();
        expect(screen.getByText('Company 1')).toBeInTheDocument();
        expect(screen.getByText('100k')).toBeInTheDocument();
        expect(screen.getByText('Created')).toBeInTheDocument();
        // Since mock jobs might not have created date set or it's old, let's just check if the column exists effectively
        // We'll check for '-' if date is missing or specific value if we set it.
        // The createMockJobs utility might not set 'created' by default to a fresh date.
        
        expect(screen.getByText('Job 2')).toBeInTheDocument();
        expect(screen.getByText('Company 2')).toBeInTheDocument();
        expect(screen.getByText('120k')).toBeInTheDocument();
    });

    it('displays lapsed time correctly with tooltip', () => {
        const now = new Date('2023-10-15T12:00:00Z');
        vi.setSystemTime(now);
        
        const createdDate = '2023-10-10T12:00:00Z';
        const jobsWithDate = [
            { ...mockJobs[0], created: createdDate }, // 5 days ago
        ];
        render(<JobTable {...defaultProps} jobs={jobsWithDate} />);
        
        const cell = screen.getByText('5d');
        expect(cell).toBeInTheDocument();

        // Helper to match local time output of dateUtils
        const date = new Date(createdDate);
        const hours = date.getHours().toString();
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const expectedTime = `${hours}:${minutes}`;

        expect(cell).toHaveAttribute('title', `5 days ago ${expectedTime}`);
    });

    it('highlights selected job', () => {
        render(<JobTable {...defaultProps} selectedJob={mockJobs[0]} />);
        const rows = screen.getAllByRole('row');
        // Header + 2 data rows. First data row should be selected.
        expect(rows[1]).toHaveClass('selected');
        expect(rows[2]).not.toHaveClass('selected');
    });

    it('calls onJobSelect when a row is clicked', () => {
        const onJobSelect = vi.fn();
        render(<JobTable {...defaultProps} onJobSelect={onJobSelect} />);

        fireEvent.click(screen.getByText('Job 1'));
        expect(onJobSelect).toHaveBeenCalledWith(mockJobs[0]);
    });

    it('does not trigger onLoadMore when container has no scrollbar', () => {
        let observerCallback: IntersectionObserverCallback | null = null;
        
        globalThis.IntersectionObserver = vi.fn(function(this: IntersectionObserver, callback: IntersectionObserverCallback) {
            observerCallback = callback;
            return {
                observe: vi.fn(),
                unobserve: vi.fn(),
                disconnect: vi.fn(),
                root: null,
                rootMargin: '',
                thresholds: [],
                takeRecords: () => [],
            };
        }) as any;

        const onLoadMore = vi.fn();
        const { container } = render(
            <JobTable 
                {...defaultProps} 
                onLoadMore={onLoadMore} 
                hasMore={true}
            />
        );

        const tableContainer = container.querySelector('.job-table-container') as HTMLDivElement;
        Object.defineProperty(tableContainer, 'scrollHeight', { value: 100, configurable: true });
        Object.defineProperty(tableContainer, 'clientHeight', { value: 100, configurable: true });

        const lastRow = container.querySelectorAll('tbody tr')[mockJobs.length - 1];
        
        if (observerCallback) {
            observerCallback([{ isIntersecting: true, target: lastRow } as IntersectionObserverEntry], {} as IntersectionObserver);
        }

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('triggers onLoadMore when container has scrollbar and last row is visible', () => {
        let observerCallback: IntersectionObserverCallback | null = null;
        
        globalThis.IntersectionObserver = vi.fn(function(this: IntersectionObserver, callback: IntersectionObserverCallback) {
            observerCallback = callback;
            return {
                observe: vi.fn(),
                unobserve: vi.fn(),
                disconnect: vi.fn(),
                root: null,
                rootMargin: '',
                thresholds: [],
                takeRecords: () => [],
            };
        }) as any;

        const onLoadMore = vi.fn();
        const { container } = render(
            <JobTable 
                {...defaultProps} 
                onLoadMore={onLoadMore} 
                hasMore={true}
            />
        );

        const tableContainer = container.querySelector('.job-table-container') as HTMLDivElement;
        Object.defineProperty(tableContainer, 'scrollHeight', { value: 200, configurable: true });
        Object.defineProperty(tableContainer, 'clientHeight', { value: 100, configurable: true });

        const lastRow = container.querySelectorAll('tbody tr')[mockJobs.length - 1];
        
        if (observerCallback) {
            observerCallback([{ isIntersecting: true, target: lastRow } as IntersectionObserverEntry], {} as IntersectionObserver);
        }

        expect(onLoadMore).toHaveBeenCalled();
    });
});
