import { vi } from 'vitest';
import { MockJobList, MockFilters, MockViewTabs, MockJobEditForm, MockReactMarkdownCustom, setupGlobalMocks } from './ViewerMocks';

vi.mock('../viewer/components/JobList', () => ({ default: MockJobList }));
vi.mock('../viewer/components/Filters', () => ({ default: MockFilters }));
vi.mock('../viewer/components/ViewTabs', () => ({ default: MockViewTabs }));
vi.mock('../viewer/components/JobEditForm', () => ({ default: MockJobEditForm }));
vi.mock('../common/components/core/ReactMarkdownCustom', () => ({ default: MockReactMarkdownCustom }));
vi.mock('../viewer/api/ViewerApi', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
        getAppliedJobsByCompany: vi.fn().mockResolvedValue([]),
    },
}));
vi.mock('../common/api/DdlApi', () => ({
    getModalityValues: vi.fn().mockResolvedValue(['REMOTE', 'HYBRID', 'ON_SITE']),
}));
vi.mock('../../hooks/viewer/useJobUpdates', () => ({
    useJobUpdates: vi.fn().mockReturnValue({ hasNewJobs: false, newJobsCount: 0, newJobIds: [] }),
}));
vi.mock('../../services/FilterConfigService', () => ({
    FilterConfigService: vi.fn().mockImplementation(function() {
        return {
            load: vi.fn().mockResolvedValue([]),
            save: vi.fn().mockResolvedValue(undefined),
            delete: vi.fn().mockResolvedValue(undefined),
            export: vi.fn().mockResolvedValue([])
        };
    })
}));

setupGlobalMocks();

import { fireEvent } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { jobsApi } from '../viewer/api/ViewerApi';
import { renderViewer } from './ViewerTestUtils';
import { mockJobsApiDefault, selectJob } from './ViewerTestHelpers';
import { runTimers, setupTestLifecycle } from './ViewerMocks';

describe('Viewer - shortcut hints', () => {
    setupTestLifecycle();

    beforeEach(() => {
        localStorage.clear();
    });

    const badgeTexts = () => Array.from(document.querySelectorAll('.shortcut-badge')).map(b => b.textContent);
    const renderWithSelection = async () => {
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        selectJob('Job 1');
        await runTimers();
    };

    it('shows job list and detail shortcut badges while Alt is held', async () => {
        await renderWithSelection();
        expect(document.querySelectorAll('.shortcut-badge').length).toBe(0);

        fireEvent.keyDown(window, { key: 'Alt' });
        await runTimers();

        const texts = badgeTexts();
        expect(texts).toContain('Alt+I');
        expect(texts).toContain('Alt+A');
        expect(texts).toContain('Alt+N');
        expect(texts).toContain('Alt+P');
        expect(texts).toContain('Alt+L');
        expect(texts).toContain('Alt+J');
        expect(texts).toContain('Alt+O');
    });

    it('keeps badges visible while Alt+letter is pressed and hides them on release', async () => {
        await renderWithSelection();

        fireEvent.keyDown(window, { key: 'Alt' });
        expect(document.querySelectorAll('.shortcut-badge').length).toBeGreaterThan(0);

        fireEvent.keyDown(window, { key: 'i', altKey: true });
        await runTimers();
        expect(jobsApi.updateJob).toHaveBeenCalledWith(1, { ignored: true });
        expect(document.querySelectorAll('.shortcut-badge').length).toBeGreaterThan(0);

        fireEvent.keyUp(window, { key: 'i', altKey: true });
        expect(document.querySelectorAll('.shortcut-badge').length).toBeGreaterThan(0);

        fireEvent.keyUp(window, { key: 'Alt' });
        await runTimers();
        expect(document.querySelectorAll('.shortcut-badge').length).toBe(0);
    });
});