import React from 'react';
import type { Job } from '../api/jobs';
import JobTable from './JobTable';

interface JobListProps {
    isLoading: boolean;
    error: unknown;
    jobs: Job[];
    selectedJob: Job | null;
    onJobSelect: (job: Job) => void;
    onLoadMore: () => void;
    isLoadingMore: boolean;
    totalResults: number;
    hasMore: boolean;
}

const JobList: React.FC<JobListProps> = ({
    isLoading,
    error,
    jobs,
    selectedJob,
    onJobSelect,
    onLoadMore,
    isLoadingMore,
    totalResults,
    hasMore
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
        <>
            <JobTable
                jobs={jobs}
                selectedJob={selectedJob}
                onJobSelect={onJobSelect}
                onLoadMore={onLoadMore}
                hasMore={hasMore}
            />
            {isLoadingMore && (
                <div className="loading-more">
                    <div className="spinner"></div>
                    <span>Loading more jobs...</span>
                </div>
            )}
            <div className="footer-info">
                Total results: {totalResults} | Showing: {jobs.length}
            </div>
        </>
    );
};

export default JobList;
