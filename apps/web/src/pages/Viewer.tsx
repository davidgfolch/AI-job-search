import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type Job, type JobListParams } from '../api/jobs';
import JobTable from '../components/JobTable';
import JobDetail from '../components/JobDetail';
import JobEditForm from '../components/JobEditForm';
import Filters from '../components/Filters';
import './Viewer.css';

type TabType = 'list' | 'edit';

export default function Viewer() {
    const queryClient = useQueryClient();
    const [filters, setFilters] = useState<JobListParams>({
        page: 1,
        size: 20,
        search: '',
        order: 'created desc',
    });
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [activeTab, setActiveTab] = useState<TabType>('list');

    const { data, isLoading, error } = useQuery({
        queryKey: ['jobs', filters],
        queryFn: () => jobsApi.getJobs(filters),
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: Partial<Job> }) =>
            jobsApi.updateJob(id, data),
        onSuccess: (updatedJob) => {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
            // Update selectedJob with the fresh data from the mutation response
            if (selectedJob && updatedJob.id === selectedJob.id) {
                setSelectedJob(updatedJob);
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

    if (error) {
        return <div className="error">Error loading jobs: {String(error)}</div>;
    }

    return (
        <div className="viewer">
            <div className="viewer-container">
                <Filters filters={filters} onFiltersChange={(newFilters) => setFilters({ ...filters, ...newFilters, page: 1 })} />
                <div className="viewer-content">
                    <div className="viewer-left">
                        <div className="tab-group">
                            <div className="tab-buttons">
                                <button
                                    className={`tab-button ${activeTab === 'list' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('list')}
                                >
                                    List
                                </button>
                                <button
                                    className={`tab-button ${activeTab === 'edit' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('edit')}
                                >
                                    Edit
                                </button>
                            </div>
                            <div className="tab-content">
                                {activeTab === 'list' ? (
                                    <>
                                        {isLoading ? (
                                            <div className="loading">Loading jobs...</div>
                                        ) : (
                                            <>
                                                <JobTable jobs={data?.items || []} selectedJob={selectedJob} onJobSelect={handleJobSelect} />
                                                <div className="pagination">
                                                    <button disabled={filters.page === 1} onClick={() => setFilters({ ...filters, page: (filters.page || 1) - 1 })}>
                                                        Previous
                                                    </button>
                                                    <span>
                                                        Page {filters.page} of {Math.ceil((data?.total || 0) / (filters.size || 20))}
                                                    </span>
                                                    <button disabled={(filters.page || 1) * (filters.size || 20) >= (data?.total || 0)}
                                                        onClick={() => setFilters({ ...filters, page: (filters.page || 1) + 1 })}>
                                                        Next
                                                    </button>
                                                </div>
                                                <div className="footer-info">
                                                    Total results: {data?.total || 0} | Showing: {data?.items.length || 0}
                                                </div>
                                            </>
                                        )}
                                    </>
                                ) : (
                                    <JobEditForm job={selectedJob} onUpdate={handleJobUpdate} />
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="viewer-right">
                        {selectedJob ? (
                            <JobDetail job={selectedJob} />
                        ) : (
                            <div className="no-selection">Select a job to view details</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
