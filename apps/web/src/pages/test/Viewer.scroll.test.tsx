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
    });

    it('loads job details when clicking a job loaded via infinite scroll', async () => {
        vi.useFakeTimers();
        (jobsApi.getJobs as any).mockImplementation((params: any) => {
            const page2Jobs = [
                { id: 3, title: 'Job 3', company: 'Company 3', description: 'Desc 3', date: '2024-01-02', markdown: 'Desc 3', created: '2024-01-02' },
                { id: 4, title: 'Job 4', company: 'Company 4', description: 'Desc 4', date: '2024-01-02', markdown: 'Desc 4', created: '2024-01-02' }
            ];
            if (params.page === 2) {
                return Promise.resolve({ items: page2Jobs, total: 4, page: 2, size: 2 });
            }
            return Promise.resolve({ items: [
                { id: 1, title: 'Job 1', company: 'Company 1', markdown: 'Desc 1', created: '2024-01-01' },
                { id: 2, title: 'Job 2', company: 'Company 2', markdown: 'Desc 2', created: '2024-01-01' }
            ], total: 4, page: 1, size: 2 });
        });
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
