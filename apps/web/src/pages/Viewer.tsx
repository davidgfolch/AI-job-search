import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type Job, type JobListParams } from '../api/jobs';
import JobTable from '../components/JobTable';
import JobDetail from '../components/JobDetail';
import JobEditForm from '../components/JobEditForm';
import Filters from '../components/Filters';
import './Viewer.css';
import Messages from '../components/Messages';

type TabType = 'list' | 'edit';

export default function Viewer() {
    const [searchParams, setSearchParams] = useSearchParams();
    const queryClient = useQueryClient();
    const [filters, setFilters] = useState<JobListParams>({
        page: 1,
        size: 20,
        search: '',
        order: 'created desc',
    });
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [activeTab, setActiveTab] = useState<TabType>('list');
    const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

    // Track when we need to auto-select next job after state change
    const autoSelectNext = useRef<{ shouldSelect: boolean; previousJobId: number | null }>({
        shouldSelect: false,
        previousJobId: null,
    });

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

    // Auto-select next job after data refetch when a state change occurred
    useEffect(() => {
        if (!autoSelectNext.current.shouldSelect || !data?.items || !autoSelectNext.current.previousJobId) {
            return;
        }
        // Find the previous job in the new data
        const previousIndex = data.items.findIndex(j => j.id === autoSelectNext.current.previousJobId);
        if (previousIndex === -1) {
            // Job was filtered out, select next available job
            if (data.items.length > 0) {
                // Try to select the job at the same index, or the last job if we're past the end
                const indexToSelect = Math.min(previousIndex >= 0 ? previousIndex : 0, data.items.length - 1);
                handleJobSelect(data.items[indexToSelect]);
            } else {
                // No jobs left in list
                setSelectedJob(null);
            }
        }
        // Reset the flag
        autoSelectNext.current = { shouldSelect: false, previousJobId: null };
    }, [data?.items]); // Trigger when data changes after refetch

    // Handle jobId URL parameter on mount
    useEffect(() => {
        const jobIdParam = searchParams.get('jobId');
        if (jobIdParam) {
            const jobId = parseInt(jobIdParam, 10);
            if (!isNaN(jobId)) {
                // Try to find the job in the current list first
                const job = data?.items.find(j => j.id === jobId);
                if (job) {
                    setSelectedJob(job);
                } else {
                    // If not in current list, fetch it directly
                    jobsApi.getJob(jobId).then(setSelectedJob).catch(console.error);
                }
            }
        }
    }, [searchParams, data?.items]);

    const handleJobSelect = (job: Job) => {
        setSelectedJob(job);
        // Update URL with jobId parameter
        const newParams = new URLSearchParams(searchParams);
        newParams.set('jobId', job.id.toString());
        setSearchParams(newParams);
    };

    const handleJobUpdate = (data: Partial<Job>) => {
        if (selectedJob) {
            // Check if any state field is being updated
            const stateFields = [
                'ignored', 'seen', 'applied', 'discarded', 'closed',
                'flagged', 'like', 'ai_enriched'
            ];
            const hasStateChange = stateFields.some(field => field in data);

            if (hasStateChange) {
                autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            }

            updateMutation.mutate({ id: selectedJob.id, data });
        }
    };

    const handleIgnoreJob = () => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { ignored: true } });
        }
    };

    const handleSeenJob = () => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { seen: true } });
        }
    };

    const handleAppliedJob = () => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { applied: true } });
        }
    };

    const handleDiscardedJob = () => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { discarded: true } });
        }
    };

    const handleClosedJob = () => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { closed: true } });
        }
    };

    const handleNextJob = () => {
        if (!data?.items || !selectedJob) return;
        const currentIndex = data.items.findIndex(j => j.id === selectedJob.id);
        if (currentIndex >= 0 && currentIndex < data.items.length - 1) {
            handleJobSelect(data.items[currentIndex + 1]);
        }
    };

    const handlePreviousJob = () => {
        if (!data?.items || !selectedJob) return;
        const currentIndex = data.items.findIndex(j => j.id === selectedJob.id);
        if (currentIndex > 0) {
            handleJobSelect(data.items[currentIndex - 1]);
        }
    };

    // Calculate navigation state
    const selectedIndex = data?.items.findIndex(j => j.id === selectedJob?.id) ?? -1;
    const hasNext = selectedIndex >= 0 && selectedIndex < (data?.items.length ?? 0) - 1;
    const hasPrevious = selectedIndex > 0;

    return (
        <div className="viewer">
            <div className="viewer-container">
                {message && (
                    <Messages
                        message={message.text}
                        type={message.type}
                        onDismiss={() => setMessage(null)}
                    />
                )}
                {error && (
                    <Messages
                        message={`Error loading jobs: ${String(error)}`}
                        type="error"
                        onDismiss={() => { }}
                    />
                )}
                <Filters
                    filters={filters}
                    onFiltersChange={(newFilters) => setFilters({ ...filters, ...newFilters, page: 1 })}
                    onMessage={(text, type) => setMessage({ text, type })}
                />
                <div className="viewer-content">
                    <div className="viewer-left">
                        <div className="tab-group">
                            <div className="tab-buttons">
                                <button className={`tab-button ${activeTab === 'list' ? 'active' : ''}`} onClick={() => setActiveTab('list')}>
                                    List
                                </button>
                                <button className={`tab-button ${activeTab === 'edit' ? 'active' : ''}`} onClick={() => setActiveTab('edit')}>
                                    Edit
                                </button>
                            </div>
                            <div className="tab-content">
                                {activeTab === 'list' ? (
                                    <>
                                        {isLoading ? (
                                            <div className="loading">
                                                <div className="spinner"></div>
                                                <span>Loading jobs...</span>
                                            </div>
                                        ) : error ? (
                                            <div className="no-data">Unable to load jobs. Please check your filters and try again.</div>
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
                            <JobDetail
                                job={selectedJob}
                                filters={filters}
                                onSeen={handleSeenJob}
                                onApplied={handleAppliedJob}
                                onDiscarded={handleDiscardedJob}
                                onClosed={handleClosedJob}
                                onIgnore={handleIgnoreJob}
                                onNext={handleNextJob}
                                onPrevious={handlePreviousJob}
                                hasNext={hasNext}
                                hasPrevious={hasPrevious}
                            />
                        ) : (
                            <div className="no-selection">Select a job to view details</div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
