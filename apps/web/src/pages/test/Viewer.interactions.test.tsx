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
import { mockJobsApiDefault, selectJob, switchToTab, clickFilterButton } from './ViewerTestHelpers';
import { runTimers, setupTestLifecycle } from './ViewerMocks';

describe('Viewer - User Interactions', () => {
    setupTestLifecycle();

    it('handles user interactions: select, verify details, partial filter', async () => {
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        expect(screen.getByText('Select a job to view details')).toBeInTheDocument();
        selectJob('Job 1');
        await runTimers();
        expect(screen.getByText('Description 1', { selector: '.markdown-content p' })).toBeInTheDocument();
        expect(screen.getAllByText('Company 1')).toHaveLength(2);
        clickFilterButton('Flagged');
        expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ flagged: true, page: 1 }));
        await runTimers();
    });

    it('handles tab switching and edit interactions', async () => {
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        expect(screen.getAllByText('Job 1').length).toBeGreaterThan(0);
        selectJob('Job 1');
        switchToTab('Edit');
        expect(screen.getByText('Edit Comments')).toBeInTheDocument();
        switchToTab('List');
        expect(screen.getByRole('cell', { name: 'Job 1' })).toBeInTheDocument();
        await runTimers();
    });

    it('filters by URL ids', async () => {
        mockJobsApiDefault();
        renderViewer(['/?ids=1,2']);
        await runTimers();
        expect(jobsApi.getJobs).toHaveBeenCalledWith(expect.objectContaining({ sql_filter: 'id IN (1,2)', page: 1 }));
    });
});
