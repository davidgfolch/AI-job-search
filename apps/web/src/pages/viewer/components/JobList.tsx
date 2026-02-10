import React from 'react';
import type { Job } from '../api/ViewerApi';
import JobTable from './JobTable';

interface JobListProps {
    isLoading: boolean;
    error: unknown;
    jobs: Job[];
    selectedJob: Job | null;
    onJobSelect: (job: Job) => void;
    onLoadMore: () => void;
    hasMore: boolean;
    selectedIds: Set<number>;
    selectionMode: 'none' | 'manual' | 'all';
    onToggleSelectJob: (id: number) => void;
    onToggleSelectAll: () => void;
}

const JobList: React.FC<JobListProps> = ({
    isLoading,
    error,
    jobs,
    selectedJob,
    onJobSelect,
    onLoadMore,
    hasMore,
    selectedIds,
    selectionMode,
    onToggleSelectJob,
    onToggleSelectAll
}) => {
    if (isLoading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <span>Loading jobs...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="no-data">Unable to load jobs. Please check your filters and try again.</div>
        );
    }

    return (
        <JobTable
            jobs={jobs}
            selectedJob={selectedJob}
            onJobSelect={onJobSelect}
            onLoadMore={onLoadMore}
            hasMore={hasMore}
            selectedIds={selectedIds}
            selectionMode={selectionMode}
            onToggleSelectJob={onToggleSelectJob}
            onToggleSelectAll={onToggleSelectAll}
        />
    );
};

export default JobList;
