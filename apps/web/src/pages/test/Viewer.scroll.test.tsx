import { vi } from 'vitest';
import { MockJobList, MockJobDetail, MockFilters, MockViewTabs, MockJobEditForm, MockJobActions, MockReactMarkdownCustom, setupGlobalMocks } from './ViewerMocks';

vi.mock('../viewer/components/JobList', () => ({ default: MockJobList }));
vi.mock('../viewer/components/JobDetail', () => ({ default: MockJobDetail }));
vi.mock('../viewer/components/Filters', () => ({ default: MockFilters }));
vi.mock('../viewer/components/ViewTabs', () => ({ default: MockViewTabs }));
vi.mock('../viewer/components/JobEditForm', () => ({ default: MockJobEditForm }));
vi.mock('../viewer/components/JobActions', () => ({ default: MockJobActions }));
vi.mock('../common/components/core/ReactMarkdownCustom', () => ({ default: MockReactMarkdownCustom }));
vi.mock('../viewer/api/ViewerApi', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
        getAppliedJobsByCompany: vi.fn().mockResolvedValue([]),
    },
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

import { screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { jobsApi } from '../viewer/api/ViewerApi';
import { renderViewer } from './ViewerTestUtils';
import { selectJob, verifySummary } from './ViewerTestHelpers';
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
        verifySummary(/2\/50 loaded/);
        expect(jobsApi.getJobs).toHaveBeenCalled();
    }, 10000);

    it('loads job details when selecting a job from the list', async () => {
        (jobsApi.getJobs as any).mockResolvedValue({
            items: [
                { id: 1, title: 'Job 1', company: 'Company 1', markdown: 'Desc 1', created: '2024-01-01' },
                { id: 2, title: 'Job 2', company: 'Company 2', markdown: 'Desc 2', created: '2024-01-01' }
            ],
            total: 2,
            page: 1,
            size: 20
        });
        (jobsApi.getJob as any).mockResolvedValue({ id: 1, title: 'Job 1', company: 'Company 1', markdown: 'Desc 1', created: '2024-01-01' });
        renderViewer();
        await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        selectJob('Job 1');
        await runTimers();
        expect(screen.getByText('Desc 1', { selector: '.markdown-content p' })).toBeInTheDocument();
    }, 10000);
});
