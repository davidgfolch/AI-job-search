import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type Job, type JobListParams } from '../api/jobs';
import JobList from '../components/JobList';
import JobDetail from '../components/JobDetail';
import JobEditForm from '../components/JobEditForm';
import JobActions from '../components/JobActions';
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
    const [allJobs, setAllJobs] = useState<Job[]>([]);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
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

    // Update allJobs when data changes
    useEffect(() => {
        if (data?.items) {
            if (filters.page === 1) {
                // Reset on first page (new search/filter)
                setAllJobs(data.items);
            } else {
                // Append on subsequent pages
                setAllJobs(prev => {
                    // Avoid duplicates
                    const newItems = data.items.filter(item => !prev.some(p => p.id === item.id));
                    return [...prev, ...newItems];
                });
            }
            setIsLoadingMore(false);
        }
    }, [data, filters.page]);

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
        if (!autoSelectNext.current.shouldSelect || !allJobs.length || !autoSelectNext.current.previousJobId) {
            return;
        }
        // Find the previous job in the new data
        const previousIndex = allJobs.findIndex(j => j.id === autoSelectNext.current.previousJobId);
        if (previousIndex === -1) {
            // Job was filtered out, select next available job
            if (allJobs.length > 0) {
                // Try to select the job at the same index, or the last job if we're past the end
                const indexToSelect = Math.min(previousIndex >= 0 ? previousIndex : 0, allJobs.length - 1);
                handleJobSelect(allJobs[indexToSelect]);
            } else {
                // No jobs left in list
                setSelectedJob(null);
            }
        }
        // Reset the flag
        autoSelectNext.current = { shouldSelect: false, previousJobId: null };
    }, [allJobs]); // Trigger when allJobs changes after refetch

    // Handle URL parameters on mount
    useEffect(() => {
        const jobIdParam = searchParams.get('jobId');
        const idsParam = searchParams.get('ids');
        if (idsParam) {
            const ids = idsParam.split(',').map(id => parseInt(id, 10)).filter(id => !isNaN(id));
            if (ids.length > 0) {
                // Check if filters already have these ids to avoid infinite loop if searchParams checks cause re-renders
                // JSON.stringify comparison is a simple way to check equality for number arrays
                setFilters(prev => {
                    if (JSON.stringify(prev.ids) === JSON.stringify(ids)) return prev;
                    return { ...prev, ids, page: 1 };
                });
            }
        }

        if (jobIdParam) {
            const jobId = parseInt(jobIdParam, 10);
            if (!isNaN(jobId)) {
                // Try to find the job in the current list first
                const job = allJobs.find(j => j.id === jobId);
                if (job) {
                    setSelectedJob(job);
                } else {
                    // If not in current list, fetch it directly
                    jobsApi.getJob(jobId).then(setSelectedJob).catch(console.error);
                }
            }
        }
    }, [searchParams, allJobs]); // Changed dependency from data?.items to allJobs which is derived from it

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
        if (!allJobs.length || !selectedJob) return;
        const currentIndex = allJobs.findIndex(j => j.id === selectedJob.id);
        if (currentIndex >= 0 && currentIndex < allJobs.length - 1) {
            handleJobSelect(allJobs[currentIndex + 1]);
        }
    };

    const handlePreviousJob = () => {
        if (!allJobs.length || !selectedJob) return;
        const currentIndex = allJobs.findIndex(j => j.id === selectedJob.id);
        if (currentIndex > 0) {
            handleJobSelect(allJobs[currentIndex - 1]);
        }
    };

    const handleLoadMore = () => {
        if (!isLoadingMore && !isLoading && allJobs.length < (data?.total || 0)) {
            setIsLoadingMore(true);
            setFilters(prev => ({ ...prev, page: (prev.page || 1) + 1 }));
        }
    };

    // Calculate navigation state
    const selectedIndex = allJobs.findIndex(j => j.id === selectedJob?.id) ?? -1;
    const hasNext = selectedIndex >= 0 && selectedIndex < allJobs.length - 1;
    const hasPrevious = selectedIndex > 0;



    return (
        <div className="viewer">
            <div className="viewer-container">
                {message && (<Messages message={message.text} type={message.type} onDismiss={() => setMessage(null)} />)}
                {error && (<Messages message={`Error loading jobs: ${String(error)}`} type="error" onDismiss={() => { }} />)}
                <Filters filters={filters} onFiltersChange={(newFilters) => setFilters({ ...filters, ...newFilters, page: 1 })}
                    onMessage={(text, type) => setMessage({ text, type })} />
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
                                {selectedJob && (
                                    <JobActions
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
                                )}
                            </div>
                            <div className="tab-content">
                                {activeTab === 'list' ? (
                                    <JobList
                                        isLoading={isLoading}
                                        error={error}
                                        jobs={allJobs}
                                        selectedJob={selectedJob}
                                        onJobSelect={handleJobSelect}
                                        onLoadMore={handleLoadMore}
                                        isLoadingMore={isLoadingMore}
                                        totalResults={data?.total || 0}
                                        hasMore={allJobs.length < (data?.total || 0)}
                                    />
                                ) : (<JobEditForm job={selectedJob} onUpdate={handleJobUpdate} />
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="viewer-right">
                        {selectedJob ? <JobDetail job={selectedJob} /> : <div className="no-selection">Select a job to view details</div>}
                    </div>
                </div>
            </div>
        </div>
    );
}
