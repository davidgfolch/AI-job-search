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
import { mockJobs, renderViewer } from './ViewerTestUtils';
import { verifySummary } from './ViewerTestHelpers';
import { runTimers, setupTestLifecycle } from './ViewerMocks';

describe('Viewer - State Management', () => {
    setupTestLifecycle();
    
    const stateTestCases = [
        {
            name: 'renders loading state initially',
            mockSetup: () => (jobsApi.getJobs as any).mockReturnValue(new Promise(() => { })),
            assertion: async () => {
                expect(screen.getByText('Loading jobs...')).toBeInTheDocument();
                await runTimers();
            }
        },
        {
            name: 'renders job list after loading',
            mockSetup: () => (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 }),
            assertion: async () => {
                await runTimers();
                expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
                verifySummary(/2\/2 loaded/);
            }
        },
        {
            name: 'handles error state',
            mockSetup: () => (jobsApi.getJobs as any).mockRejectedValue(new Error('Failed to fetch')),
            assertion: async () => {
                await runTimers();
                expect(screen.getAllByText('Failed to fetch').length).toBeGreaterThan(0);
            }
        }
    ];
    
    it.each(stateTestCases)('$name', async ({ mockSetup, assertion }) => {
        mockSetup();
        renderViewer();
        await assertion();
    });
});
