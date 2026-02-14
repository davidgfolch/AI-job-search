import { renderHook, act } from '@testing-library/react';
import { useAppliedModal } from '../useAppliedModal';
import { type Job } from '../../api/ViewerApi';

vi.mock('../../api/ViewerApi', () => ({
    jobsApi: {
        getJob: vi.fn(),
    },
}));

const createMockJob = (overrides: Partial<Job> = {}): Job => ({
    id: 1,
    title: 'Test Job',
    company: 'Test Company',
    comments: null,
    applied: false,
    salary: null,
    location: null,
    url: null,
    markdown: null,
    web_page: null,
    created: '2023-01-01',
    modified: null,
    flagged: false,
    like: false,
    ignored: false,
    seen: false,
    discarded: false,
    closed: false,
    client: null,
    required_technologies: null,
    optional_technologies: null,
    ai_enriched: false,
    ai_enrich_error: null,
    duplicated_id: null,
    ...overrides,
});

const createMockProps = (overrides = {}) => ({
    selectedJob: createMockJob(),
    allJobs: [createMockJob()],
    onJobUpdate: vi.fn(),
    onBulkUpdate: vi.fn(),
    selectedIds: new Set<number>(),
    selectionMode: 'none' as const,
    ...overrides,
});

describe('useAppliedModal', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should start with modal closed', () => {
        const { result } = renderHook(() => useAppliedModal(createMockProps()));
        expect(result.current.isModalOpen).toBe(false);
    });

    it('should open modal for single job mode', () => {
        const { result } = renderHook(() => useAppliedModal(createMockProps()));
        act(() => { result.current.openModal(); });
        expect(result.current.isModalOpen).toBe(true);
    });

    const openModalTestCases = [
        { name: 'single selection in bulk mode', props: { selectionMode: 'manual' as const, selectedIds: new Set([1]) }, shouldOpen: true },
        { name: 'multiple selection', props: { selectionMode: 'manual' as const, selectedIds: new Set([1, 2]) }, shouldOpen: false },
        { name: '"all" selection', props: { selectionMode: 'all' as const }, shouldOpen: false },
    ];

    openModalTestCases.forEach(({ name, props, shouldOpen }) => {
        it(`should ${shouldOpen ? '' : 'not '}open modal for ${name}`, () => {
            const { result } = renderHook(() => useAppliedModal(createMockProps(props)));
            act(() => { result.current.openModal(); });
            expect(result.current.isModalOpen).toBe(shouldOpen);
        });
    });

    const confirmationTestCases = [
        { name: 'with comment', hasComment: true, comment: '- applied with comment', expected: { applied: true, comments: '- applied with comment' } },
        { name: 'without comment', hasComment: false, comment: '', expected: { applied: true } },
    ];

    confirmationTestCases.forEach(({ name, hasComment, comment, expected }) => {
        it(`should handle single job confirmation ${name}`, async () => {
            const onJobUpdate = vi.fn();
            const { result } = renderHook(() => useAppliedModal(createMockProps({ onJobUpdate })));
            act(() => { result.current.openModal(); });
            await act(async () => { await result.current.handleConfirm(hasComment, comment); });
            expect(onJobUpdate).toHaveBeenCalledWith(expected);
            expect(result.current.isModalOpen).toBe(false);
        });
    });

    it('should append comment to existing comments for single job', async () => {
        const onJobUpdate = vi.fn();
        const jobWithExistingComment = createMockJob({ comments: 'existing comment' });
        const { result } = renderHook(() => useAppliedModal(createMockProps({ selectedJob: jobWithExistingComment, onJobUpdate })));
        act(() => { result.current.openModal(); });
        await act(async () => { await result.current.handleConfirm(true, '- applied with new comment'); });
        expect(onJobUpdate).toHaveBeenCalledWith({ applied: true, comments: 'existing comment - applied with new comment' });
    });

    it('should handle bulk confirmation with comment', async () => {
        const onBulkUpdate = vi.fn();
        const { result } = renderHook(() => useAppliedModal(createMockProps({
            selectedJob: null,
            selectionMode: 'manual' as const,
            selectedIds: new Set([1]),
            onBulkUpdate,
        })));
        act(() => { result.current.openModal(); });
        await act(async () => { await result.current.handleConfirm(true, '- bulk applied'); });
        expect(onBulkUpdate).toHaveBeenCalledWith([1], { applied: true, comments: '- bulk applied' });
        expect(result.current.isModalOpen).toBe(false);
    });

    it('should handle cancellation', () => {
        const { result } = renderHook(() => useAppliedModal(createMockProps()));
        act(() => { result.current.openModal(); });
        act(() => { result.current.handleCancel(); });
        expect(result.current.isModalOpen).toBe(false);
    });

    it('should close modal after confirmation', async () => {
        const { result } = renderHook(() => useAppliedModal(createMockProps()));
        act(() => { result.current.openModal(); });
        expect(result.current.isModalOpen).toBe(true);
        await act(async () => { await result.current.handleConfirm(true, 'test comment'); });
        expect(result.current.isModalOpen).toBe(false);
    });
});
