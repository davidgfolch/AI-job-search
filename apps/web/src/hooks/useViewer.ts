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
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
    const [selectionMode, setSelectionMode] = useState<'none' | 'manual' | 'all'>('none');
    
    // Modal State
    const [confirmModal, setConfirmModal] = useState<{
        isOpen: boolean;
        message: string;
        onConfirm: () => void;
    }>({ isOpen: false, message: '', onConfirm: () => {} });

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
            if (filters.page === 1) { // Reset on first page (new search/filter)
                setAllJobs(data.items);
            } else { // Append on subsequent pages
                setAllJobs(prev => { // Avoid duplicates
                    const newItems = data.items.filter(item => !prev.some(p => p.id === item.id));
                    return [...prev, ...newItems];
                });
            }
            setIsLoadingMore(false);
        }
    }, [data, filters.page]);

    // Reset selection when filters change (except page)
    useEffect(() => {
        setSelectionMode('none');
        setSelectedIds(new Set());
    }, [filters.search, filters.status, filters.not_status, filters.days_old, filters.salary, filters.order, filters.sql_filter]);

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: number; data: Partial<Job> }) =>
            jobsApi.updateJob(id, data),
        onSuccess: (updatedJob) => {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
            if (selectedJob && updatedJob.id === selectedJob.id) { // Update selectedJob with the fresh data from the mutation response
                setSelectedJob(updatedJob);
            }
        },
    });

    const bulkUpdateMutation = useMutation({
        mutationFn: (payload: { ids?: number[]; filters?: JobListParams; update: Partial<Job>; select_all?: boolean }) =>
            jobsApi.bulkUpdateJobs(payload),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
            setMessage({ text: `Updated ${data.updated} jobs`, type: 'success' });
            setSelectionMode('none');
            setSelectedIds(new Set());
        },
        onError: (err) => {
            setMessage({ text: err instanceof Error ? err.message : 'Error updating jobs', type: 'error' });
        }
    });

    const handleJobSelect = useCallback((job: Job) => {
        setSelectedJob(job);
        // Sync selection state with the clicked job
        setSelectedIds(new Set([job.id]));
        setSelectionMode('manual');
        // Update URL with jobId parameter
        const newParams = new URLSearchParams(searchParams);
        newParams.set('jobId', job.id.toString());
        setSearchParams(newParams);
    }, [searchParams, setSearchParams]);

    // Track if we are in the middle of an auto-selection to prevent race conditions with URL effect
    const isAutoSelecting = useRef(false);

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
                isAutoSelecting.current = true;
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
        if (isAutoSelecting.current) {
            isAutoSelecting.current = false;
            return;
        }
        const jobIdParam = searchParams.get('jobId');
        const idsParam = searchParams.get('ids');
        if (idsParam) {
            const ids = idsParam.split(',').map(id => parseInt(id, 10)).filter(id => !isNaN(id));
            if (ids.length > 0) {
                const sqlFilter = `id IN (${ids.join(',')})`;
                setFilters(prev => {
                    if (prev.sql_filter === sqlFilter) return prev;
                    return { ...prev, sql_filter: sqlFilter, page: 1 };
                });
                // Remove ids from URL so form works properly
                setSearchParams(prev => {
                    const newParams = new URLSearchParams(prev);
                    newParams.delete('ids');
                    return newParams;
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
            if (hasStateChange && activeTab === 'list') {
                autoSelectNext.current = { shouldSelect: true, previousJobId: selectedJob.id };
            }
            updateMutation.mutate({ id: selectedJob.id, data });
        }
    }, [selectedJob, updateMutation, activeTab]);

    const navigateJob = useCallback((direction: 'next' | 'previous') => {
        if (!allJobs.length || !selectedJob) return;
        const currentIndex = allJobs.findIndex(j => j.id === selectedJob.id);
        if (currentIndex === -1) return;
        const nextIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1;
        if (nextIndex >= 0 && nextIndex < allJobs.length) {
            handleJobSelect(allJobs[nextIndex]);
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
        state: {
            filters,
            allJobs,
            selectedJob,
            activeTab,
            message,
            data,
            selectedIds,
            selectionMode,
            confirmModal,
        },
        status: {
            isLoading,
            isLoadingMore,
            error,
            hasNext,
            hasPrevious,
        },
        actions: {
            setFilters,
            setActiveTab,
            setMessage,
            selectJob: handleJobSelect,
            updateJob: handleJobUpdate,
            ignoreJob: () => handleJobUpdate({ ignored: true }),
            seenJob: () => handleJobUpdate({ seen: true }),
            appliedJob: () => handleJobUpdate({ applied: true }),
            discardedJob: () => handleJobUpdate({ discarded: true }),
            closedJob: () => handleJobUpdate({ closed: true }),
            nextJob: () => navigateJob('next'),
            previousJob: () => navigateJob('previous'),
            loadMore: handleLoadMore,
            toggleSelectJob: (id: number) => {
                const newSelected = new Set(selectedIds);
                if (newSelected.has(id)) {
                    newSelected.delete(id);
                    if (selectionMode === 'all') setSelectionMode('manual');
                } else {
                    newSelected.add(id);
                    setSelectionMode('manual');
                }
                setSelectedIds(newSelected);
            },
            toggleSelectAll: () => {
                if (selectionMode === 'all') {
                    setSelectionMode('none');
                    setSelectedIds(new Set());
                } else {
                    setSelectionMode('all');
                }
            },
            ignoreSelected: () => {
                const count = selectionMode === 'all' ? 'all' : selectedIds.size;
                const message = selectionMode === 'all' 
                    ? "Are you sure you want to ignore ALL jobs matching the current filters?"
                    : `Are you sure you want to ignore ${count} selected jobs?`;

                setConfirmModal({
                    isOpen: true,
                    message,
                    onConfirm: () => {
                        if (selectionMode === 'all') {
                            bulkUpdateMutation.mutate({ select_all: true, filters, update: { ignored: true } });
                        } else if (selectedIds.size > 0) {
                            bulkUpdateMutation.mutate({ ids: Array.from(selectedIds), update: { ignored: true } });
                        }
                        setConfirmModal(prev => ({ ...prev, isOpen: false }));
                    }
                });
            },
            closeConfirmModal: () => setConfirmModal(prev => ({ ...prev, isOpen: false })),
        },
    };
};
