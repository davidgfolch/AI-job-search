import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import JobTable from "../JobTable";
import { createMockJobs, stubElementRect } from "../../test/test-utils";
import { createRef } from 'react';

const mockJobs = createMockJobs(2, {
    required_technologies: 'React',
    optional_technologies: 'Python',
});

let intersectionCallback: IntersectionObserverCallback | null = null;
let observedNodes: Element[] = [];

const installIntersectionObserverMock = () => {
    intersectionCallback = null;
    observedNodes = [];
    globalThis.IntersectionObserver = vi.fn(function(this: IntersectionObserver, callback: IntersectionObserverCallback) {
        intersectionCallback = callback;
        return {
            observe: vi.fn((node: Element) => { observedNodes.push(node); }),
            unobserve: vi.fn(),
            disconnect: vi.fn(),
            root: null,
            rootMargin: '',
            thresholds: [],
            takeRecords: () => [],
        };
    }) as any;
};

const scrollToBottom = () => act(() => {
    intersectionCallback!([{ isIntersecting: true, target: observedNodes[0] } as IntersectionObserverEntry], {} as IntersectionObserver);
});

/** Places the end of the list `bottom` pixels from the top of the viewport. */
const setSentinelBottom = (sentinel: HTMLElement, bottom: number) => {
    sentinel.getBoundingClientRect = () => ({ bottom, width: 100, height: 1, top: bottom - 1, left: 0, right: 100, x: 0, y: bottom - 1, toJSON: () => ({}) }) as DOMRect;
};

const ON_SCREEN_BOTTOM = 500;
const OFF_SCREEN_BOTTOM = 5000;

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

describe('JobTable', () => {
    beforeEach(() => {
        vi.useFakeTimers();
        Element.prototype.scrollIntoView = vi.fn();
        installIntersectionObserverMock();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('renders job list correctly', () => {
        render(<JobTable {...defaultProps} />);

        expect(screen.getByText('Job 1')).toBeInTheDocument();
        expect(screen.getByText('Company 1')).toBeInTheDocument();
        expect(screen.getByText('100k')).toBeInTheDocument();
        expect(screen.getByText('Created')).toBeInTheDocument();
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
        expect(cell).toHaveAttribute('title', '5 days ago 14:00');
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

    it('triggers onLoadMore when the end of the list is already on screen', async () => {
        const onLoadMore = vi.fn();
        const { container } = render(<JobTable {...defaultProps} onLoadMore={onLoadMore} hasMore={true} />);
        setSentinelBottom(container.querySelector('.job-table-sentinel') as HTMLDivElement, ON_SCREEN_BOTTOM);

        await act(async () => { await vi.advanceTimersByTimeAsync(50); });

        expect(onLoadMore).toHaveBeenCalled();
    });

    it('does not trigger onLoadMore when the end of the list is off screen and there are no more pages', async () => {
        const onLoadMore = vi.fn();
        const { container } = render(<JobTable {...defaultProps} onLoadMore={onLoadMore} hasMore={false} />);
        setSentinelBottom(container.querySelector('.job-table-sentinel') as HTMLDivElement, OFF_SCREEN_BOTTOM);

        await act(async () => { await vi.advanceTimersByTimeAsync(50); });

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('triggers onLoadMore when the bottom of the list scrolls into view', () => {
        const onLoadMore = vi.fn();
        render(<JobTable {...defaultProps} onLoadMore={onLoadMore} hasMore={true} />);

        scrollToBottom();

        expect(onLoadMore).toHaveBeenCalled();
    });

    it('does not trigger onLoadMore while a page is already loading', () => {
        const onLoadMore = vi.fn();
        render(<JobTable {...defaultProps} onLoadMore={onLoadMore} hasMore={true} isLoadingMore={true} />);

        scrollToBottom();

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('keeps watching the bottom of the list after a page is appended', () => {
        const onLoadMore = vi.fn();
        const { container, rerender } = render(<JobTable {...defaultProps} onLoadMore={onLoadMore} hasMore={true} />);
        const sentinel = container.querySelector('.job-table-sentinel') as HTMLDivElement;

        scrollToBottom();
        expect(onLoadMore).toHaveBeenCalledTimes(1);

        // A new page pushes the previous last row into the middle of the list. The observer must stay on
        // the stable bottom marker, otherwise scrolling stops loading anything.
        rerender(<JobTable {...defaultProps} jobs={createMockJobs(4, {})} onLoadMore={onLoadMore} hasMore={true} />);

        expect(observedNodes).toEqual([sentinel]);
        expect(globalThis.IntersectionObserver).toHaveBeenCalledTimes(1);
        scrollToBottom();
        expect(onLoadMore).toHaveBeenCalledTimes(2);
    });

    it('scrolls the list so a selected row outside the visible frame becomes readable', () => {
        const containerRef = createRef<HTMLDivElement>();
        const { container, rerender } = render(<JobTable {...defaultProps} containerRef={containerRef} />);
        const list = container.querySelector('.job-table-container') as HTMLDivElement;
        stubElementRect(list, { top: 100, bottom: 200 });
        stubElementRect(container.querySelector('thead')!, { top: 100, bottom: 130 });
        stubElementRect(container.querySelector('#job-row-2')!, { top: 210, bottom: 230 });

        rerender(<JobTable {...defaultProps} containerRef={containerRef} selectedJob={mockJobs[1]} />);

        // 30px below the bottom edge of a 100px list. Aligning the row with the edge instead, which is what
        // scrollIntoView does, leaves it 10px short of the frame, and an upward step would park it under the
        // sticky header.
        expect(list.scrollTop).toBe(30);
    });
});
