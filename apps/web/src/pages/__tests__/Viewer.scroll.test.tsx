import { vi } from 'vitest';
import { MockJobList, MockJobDetail, MockFilters, MockViewTabs, MockJobEditForm, MockJobActions, MockReactMarkdownCustom, setupGlobalMocks } from './ViewerMocks';

vi.mock('../../components/JobList', () => ({ default: MockJobList }));
vi.mock('../../components/JobDetail', () => ({ default: MockJobDetail }));
vi.mock('../../components/Filters', () => ({ default: MockFilters }));
vi.mock('../../components/ViewTabs', () => ({ default: MockViewTabs }));
vi.mock('../../components/JobEditForm', () => ({ default: MockJobEditForm }));
vi.mock('../../components/JobActions', () => ({ default: MockJobActions }));
vi.mock('../../components/core/ReactMarkdownCustom', () => ({ default: MockReactMarkdownCustom }));
vi.mock('../../api/jobs', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
        getAppliedJobsByCompany: vi.fn().mockResolvedValue([]),
    },
}));
vi.mock('../../hooks/viewer/useJobUpdates', () => ({
    useJobUpdates: vi.fn().mockReturnValue({ hasNewJobs: false, newJobsCount: 0 }),
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

import { screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { jobsApi } from '../../api/jobs';
import { renderViewer } from './ViewerTestUtils';
import { mockJobsApiDefault, selectJob, switchToTab, verifySummary } from './ViewerTestHelpers';
import { runTimers, setupTestLifecycle } from './ViewerMocks';

describe('Viewer - Scroll and Pagination', () => {
    setupTestLifecycle();

    it('handles infinite scroll', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: [
            { id: 1, title: 'Job 1', company: 'Company 1', markdown: 'Desc 1', created: '2024-01-01' },
            { id: 2, title: 'Job 2', company: 'Company 2', markdown: 'Desc 2', created: '2024-01-01' }
        ], total: 50, page: 1, size: 20 });
        renderViewer();
        await runTimers();
        verifySummary(/2\/50 loaded\|0 Selected/);
        expect(jobsApi.getJobs).toHaveBeenCalledTimes(1);
    });

    it('refreshes list when clicking List tab if new jobs exist', async () => {
        const { useJobUpdates } = await import('../../hooks/viewer/useJobUpdates');
        (useJobUpdates as any).mockReturnValue({ hasNewJobs: true, newJobsCount: 5 });
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        selectJob('Job 1');
        switchToTab('Edit');
        expect(screen.getByText('Edit Comments')).toBeInTheDocument();
        (jobsApi.getJobs as any).mockClear();
        const reloadBtn = screen.getByText((content, element) => element?.tagName.toLowerCase() === 'button' && content.includes('new'));
        fireEvent.click(reloadBtn);
        await runTimers();
        expect(jobsApi.getJobs).toHaveBeenCalled();
    });

    it('loads job details when clicking a job loaded via infinite scroll', async () => {
        vi.useFakeTimers();
        (jobsApi.getJobs as any).mockResolvedValueOnce({ items: [
            { id: 1, title: 'Job 1', company: 'Company 1', markdown: 'Desc 1', created: '2024-01-01' },
            { id: 2, title: 'Job 2', company: 'Company 2', markdown: 'Desc 2', created: '2024-01-01' }
        ], total: 4, page: 1, size: 2 });
        const page2Jobs = [
            { id: 3, title: 'Job 3', company: 'Company 3', description: 'Desc 3', date: '2024-01-02', markdown: 'Desc 3', created: '2024-01-02' },
            { id: 4, title: 'Job 4', company: 'Company 4', description: 'Desc 4', date: '2024-01-02', markdown: 'Desc 4', created: '2024-01-02' }
        ];
        (jobsApi.getJobs as any).mockResolvedValueOnce({ items: page2Jobs, total: 4, page: 2, size: 2 });
        (jobsApi.getAppliedJobsByCompany as any).mockResolvedValue([]);
        renderViewer();
        await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        fireEvent.click(screen.getByText('Load More'));
        await runTimers();
        expect(screen.getByText('Job 3')).toBeInTheDocument();
        selectJob('Job 3');
        await runTimers();
        expect(screen.getByText('Desc 3', { selector: '.markdown-content p' })).toBeInTheDocument();
    });
});
