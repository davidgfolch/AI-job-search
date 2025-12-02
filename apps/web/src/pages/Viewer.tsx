import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type Job, type JobListParams } from '../api/jobs';
import JobTable from '../components/JobTable';
import JobDetail from '../components/JobDetail';
import './Viewer.css';

export default function Viewer() {
    const queryClient = useQueryClient();
    const [filters, setFilters] = useState<JobListParams>({
        page: 1,
        size: 20,
        search: '',
        status: 'ai_enriched',
        not_status: 'seen,ignored,applied,discarded,closed',
    });
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);

    const { data, isLoading, error } = useQuery({
        queryKey: ['jobs', filters],
        queryFn: () => jobsApi.getJobs(filters),
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: Partial<Job> }) =>
            jobsApi.updateJob(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
            if (selectedJob) {
                // Refresh selected job
                jobsApi.getJob(selectedJob.id).then(setSelectedJob);
            }
        },
    });

    const handleJobSelect = (job: Job) => {
        setSelectedJob(job);
    };

    const handleJobUpdate = (data: Partial<Job>) => {
        if (selectedJob) {
            updateMutation.mutate({ id: selectedJob.id, data });
        }
    };

    const handleSearchChange = (search: string) => {
        setFilters({ ...filters, search, page: 1 });
    };

    if (error) {
        return <div className="error">Error loading jobs: {String(error)}</div>;
    }

    return (
        <div className="viewer">
            <div className="viewer-container">
                <div className="viewer-left">
                    <div className="filters">
                        <input
                            type="text"
                            placeholder="Search jobs..."
                            value={filters.search}
                            onChange={(e) => handleSearchChange(e.target.value)}
                            className="search-input"
                        />
                    </div>

                    {isLoading ? (
                        <div className="loading">Loading jobs...</div>
                    ) : (
                        <>
                            <JobTable
                                jobs={data?.items || []}
                                selectedJob={selectedJob}
                                onJobSelect={handleJobSelect}
                            />
                            <div className="pagination">
                                <button
                                    disabled={filters.page === 1}
                                    onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}
                                >
                                    Previous
                                </button>
                                <span>
                                    Page {filters.page} of {Math.ceil((data?.total || 0) / (filters.size || 20))}
                                </span>
                                <button
                                    disabled={(filters.page || 1) * (filters.size || 20) >= (data?.total || 0)}
                                    onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}
                                >
                                    Next
                                </button>
                            </div>
                            <div className="footer-info">
                                Total results: {data?.total || 0} | Showing: {data?.items.length || 0}
                            </div>
                        </>
                    )}
                </div>

                <div className="viewer-right">
                    {selectedJob ? (
                        <JobDetail job={selectedJob} onUpdate={handleJobUpdate} />
                    ) : (
                        <div className="no-selection">Select a job to view details</div>
                    )}
                </div>
            </div>
        </div>
    );
}
