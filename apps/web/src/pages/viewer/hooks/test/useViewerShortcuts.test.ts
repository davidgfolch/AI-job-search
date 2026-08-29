import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useViewerShortcuts } from '../useViewerShortcuts';
import type { Job } from '../../api/ViewerApi';

const makeActions = () => ({
    ignoreJob: vi.fn(),
    ignoreSelected: vi.fn(),
    appliedJob: vi.fn(),
    nextJob: vi.fn(),
    previousJob: vi.fn(),
});

const makeJob = (overrides: Partial<Job> = {}) => ({ id: 1, url: 'https://example.com/job', ...overrides } as Job);

const render = (actions = makeActions(), selectedJob: Job | null = null, isBulk = false, jobListRef: { current: HTMLDivElement | null } = { current: null }, detailScrollRef: { current: HTMLDivElement | null } = { current: null }) => {
    const { result } = renderHook(() => useViewerShortcuts(actions, selectedJob, isBulk, jobListRef, detailScrollRef));
    return { actions, result };
};

describe('useViewerShortcuts', () => {
    it('maps job actions', () => {
        const { actions, result } = render();
        result.current('ignore');
        result.current('apply');
        result.current('next');
        result.current('previous');
        expect(actions.ignoreJob).toHaveBeenCalledTimes(1);
        expect(actions.appliedJob).toHaveBeenCalledTimes(1);
        expect(actions.nextJob).toHaveBeenCalledTimes(1);
        expect(actions.previousJob).toHaveBeenCalledTimes(1);
    });

    it('calls ignoreSelected when bulk', () => {
        const { actions, result } = render(makeActions(), null, true);
        result.current('ignore');
        expect(actions.ignoreSelected).toHaveBeenCalledTimes(1);
        expect(actions.ignoreJob).not.toHaveBeenCalled();
    });

    it('opens the selected job url on openUrl', () => {
        const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
        try {
            const { result } = render(makeActions(), makeJob());
            result.current('openUrl');
            expect(openSpy).toHaveBeenCalledWith('https://example.com/job', '_blank');
        } finally {
            openSpy.mockRestore();
        }
    });

    it('does not open when job has no url', () => {
        const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null);
        try {
            const { result } = render(makeActions(), makeJob({ url: null }));
            result.current('openUrl');
            expect(openSpy).not.toHaveBeenCalled();
        } finally {
            openSpy.mockRestore();
        }
    });

    it('focuses list and detail scroll refs on focus actions', () => {
        const listFocus = vi.fn();
        const detailFocus = vi.fn();
        const jobListRef = { current: { focus: listFocus } as unknown as HTMLDivElement };
        const detailScrollRef = { current: { focus: detailFocus } as unknown as HTMLDivElement };
        const { result } = render(makeActions(), null, false, jobListRef, detailScrollRef);
        result.current('listFocus');
        result.current('detailFocus');
        expect(listFocus).toHaveBeenCalledWith({ preventScroll: true });
        expect(detailFocus).toHaveBeenCalledWith({ preventScroll: true });
    });
});
