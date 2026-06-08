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
vi.mock('../common/api/DdlApi', () => ({
    getModalityValues: vi.fn().mockResolvedValue(['REMOTE', 'HYBRID', 'ON_SITE']),
}));
vi.mock('../../hooks/viewer/useJobUpdates', () => ({
    useJobUpdates: vi.fn().mockReturnValue({ hasNewJobs: false, newJobsCount: 0, newJobIds: [] }),
}));
vi.mock('../../services/FilterConfigService', () => ({
    FilterConfigService: vi.fn().mockImplementation(function () {
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
import { mockJobsApiDefault } from './ViewerTestHelpers';
import { renderViewer } from './ViewerTestUtils';
import { runTimers, setupTestLifecycle } from './ViewerMocks';

describe('Viewer - Collapsible Panels', () => {
    setupTestLifecycle();

    it('shows both collapse buttons when both panels are visible', async () => {
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        expect(screen.getByTitle('Collapse list')).toBeInTheDocument();
        expect(screen.getByTitle('Collapse detail')).toBeInTheDocument();
        expect(screen.queryByTitle('Show both panels')).not.toBeInTheDocument();
    });

    it('collapses left panel and shows restore + right collapse button', async () => {
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        fireEvent.click(screen.getByTitle('Collapse list'));
        expect(screen.queryByTitle('Collapse list')).not.toBeInTheDocument();
        expect(screen.getByTitle('Show both panels')).toBeInTheDocument();
        expect(screen.getByTitle('Collapse detail')).toBeInTheDocument();
    });

    it('collapses right panel and shows restore + left collapse button', async () => {
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        fireEvent.click(screen.getByTitle('Collapse detail'));
        expect(screen.queryByTitle('Collapse detail')).not.toBeInTheDocument();
        expect(screen.getByTitle('Show both panels')).toBeInTheDocument();
        expect(screen.getByTitle('Collapse list')).toBeInTheDocument();
    });

    it('restores both panels from left-collapsed state', async () => {
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        fireEvent.click(screen.getByTitle('Collapse list'));
        fireEvent.click(screen.getByTitle('Show both panels'));
        expect(screen.getByTitle('Collapse list')).toBeInTheDocument();
        expect(screen.getByTitle('Collapse detail')).toBeInTheDocument();
        expect(screen.queryByTitle('Show both panels')).not.toBeInTheDocument();
    });

    it('restores both panels from right-collapsed state', async () => {
        mockJobsApiDefault();
        renderViewer();
        await runTimers();
        fireEvent.click(screen.getByTitle('Collapse detail'));
        fireEvent.click(screen.getByTitle('Show both panels'));
        expect(screen.getByTitle('Collapse list')).toBeInTheDocument();
        expect(screen.getByTitle('Collapse detail')).toBeInTheDocument();
        expect(screen.queryByTitle('Show both panels')).not.toBeInTheDocument();
    });
});
