import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type Job, type JobListParams } from '../api/jobs';

export type TabType = 'list' | 'edit';

export const useViewer = () => {
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

    const handleJobSelect = useCallback((job: Job) => {
        setSelectedJob(job);
        // Update URL with jobId parameter
        const newParams = new URLSearchParams(searchParams);
        newParams.set('jobId', job.id.toString());
        setSearchParams(newParams);
    }, [searchParams, setSearchParams]);

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
    }, [allJobs, handleJobSelect]);

    // Handle URL parameters on mount
    useEffect(() => {
        const jobIdParam = searchParams.get('jobId');
        const idsParam = searchParams.get('ids');
        if (idsParam) {
            const ids = idsParam.split(',').map(id => parseInt(id, 10)).filter(id => !isNaN(id));
            if (ids.length > 0) {
                // Check if filters already have these ids to avoid infinite loop
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
    }, [searchParams, allJobs]);

    const handleJobUpdate = useCallback((data: Partial<Job>) => {
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
    }, [selectedJob, updateMutation]);

    const handleIgnoreJob = useCallback(() => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { ignored: true } });
        }
    }, [selectedJob, updateMutation]);

    const handleSeenJob = useCallback(() => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { seen: true } });
        }
    }, [selectedJob, updateMutation]);

    const handleAppliedJob = useCallback(() => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { applied: true } });
        }
    }, [selectedJob, updateMutation]);

    const handleDiscardedJob = useCallback(() => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { discarded: true } });
        }
    }, [selectedJob, updateMutation]);

    const handleClosedJob = useCallback(() => {
        if (selectedJob) {
            autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            updateMutation.mutate({ id: selectedJob.id, data: { closed: true } });
        }
    }, [selectedJob, updateMutation]);

    const handleNextJob = useCallback(() => {
        if (!allJobs.length || !selectedJob) return;
        const currentIndex = allJobs.findIndex(j => j.id === selectedJob.id);
        if (currentIndex >= 0 && currentIndex < allJobs.length - 1) {
            handleJobSelect(allJobs[currentIndex + 1]);
        }
    }, [allJobs, selectedJob, handleJobSelect]);

    const handlePreviousJob = useCallback(() => {
        if (!allJobs.length || !selectedJob) return;
        const currentIndex = allJobs.findIndex(j => j.id === selectedJob.id);
        if (currentIndex > 0) {
            handleJobSelect(allJobs[currentIndex - 1]);
        }
    }, [allJobs, selectedJob, handleJobSelect]);

    const handleLoadMore = useCallback(() => {
        if (!isLoadingMore && !isLoading && allJobs.length < (data?.total || 0)) {
            setIsLoadingMore(true);
            setFilters(prev => ({ ...prev, page: (prev.page || 1) + 1 }));
        }
    }, [isLoadingMore, isLoading, allJobs.length, data?.total]);

    // Calculate navigation state
    const selectedIndex = allJobs.findIndex(j => j.id === selectedJob?.id) ?? -1;
    const hasNext = selectedIndex >= 0 && selectedIndex < allJobs.length - 1;
    const hasPrevious = selectedIndex > 0;

    return {
        // State
        filters,
        setFilters,
        allJobs,
        isLoadingMore,
        selectedJob,
        activeTab,
        setActiveTab,
        message,
        setMessage,
        isLoading,
        error,
        data,

        // Handlers
        handleJobSelect,
        handleJobUpdate,
        handleIgnoreJob,
        handleSeenJob,
        handleAppliedJob,
        handleDiscardedJob,
        handleClosedJob,
        handleNextJob,
        handlePreviousJob,
        handleLoadMore,

        // Derived
        hasNext,
        hasPrevious,
    };
};
