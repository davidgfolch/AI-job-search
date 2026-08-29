import { vi } from 'vitest';
import { MockSelectableJobList, MockFilters, MockViewTabs, MockJobEditForm, MockReactMarkdownCustom, setupGlobalMocks, runTimers, setupTestLifecycle } from './ViewerMocks';

vi.mock('../viewer/components/Filters', () => ({ default: MockFilters }));
vi.mock('../viewer/components/ViewTabs', () => ({ default: MockViewTabs }));
vi.mock('../viewer/components/JobEditForm', () => ({ default: MockJobEditForm }));
vi.mock('../common/components/core/ReactMarkdownCustom', () => ({ default: MockReactMarkdownCustom }));
vi.mock('../viewer/api/ViewerApi', () => ({
    jobsApi: {
        getJobs: vi.fn(),
        getJob: vi.fn(),
        updateJob: vi.fn(),
        bulkUpdateJobs: vi.fn(),
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

vi.mock('../viewer/components/JobList', () => ({ default: MockSelectableJobList }));

setupGlobalMocks();

import { fireEvent, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { jobsApi } from '../viewer/api/ViewerApi';
import { mockJobs, renderViewer } from './ViewerTestUtils';

describe('Viewer - multi-select ignore via shortcut', () => {
    setupTestLifecycle();

    beforeEach(() => {
        localStorage.clear();
    });

    const renderAndSelect = async () => {
        (jobsApi.getJobs as any).mockResolvedValue({ items: mockJobs, total: 2, page: 1, size: 20 });
        (jobsApi.bulkUpdateJobs as any).mockResolvedValue({ updated: 2 });
        renderViewer();
        await runTimers();
        fireEvent.click(screen.getByLabelText('Select Job 1'));
        fireEvent.click(screen.getByLabelText('Select Job 2'));
        await runTimers();
    };

    it('ignores all selected jobs on ALT+I after confirming', async () => {
        await renderAndSelect();

        fireEvent.keyDown(window, { key: 'i', altKey: true });
        await runTimers();

        expect(screen.getByText(/Are you sure you want to ignore 2 selected jobs\?/)).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));
        await runTimers();

        expect(jobsApi.bulkUpdateJobs).toHaveBeenCalledWith({
            ids: [1, 2],
            update: { ignored: true },
        });
    });
});
