import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { type Job, type JobListParams } from '../api/ViewerApi';

interface UseJobSelectionProps {
    allJobs: Job[];
    filters: JobListParams;
    setFilters: React.Dispatch<React.SetStateAction<JobListParams>>;
    onLoadMore?: () => void;
    hasMorePages?: boolean;
}

export const useJobSelection = ({ allJobs, filters, setFilters, onLoadMore, hasMorePages }: UseJobSelectionProps) => {
    const [searchParams, setSearchParams] = useSearchParams();
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
    const [selectedIdxs, setSelectedIdxs] = useState<Set<number>>(new Set());
    const [selectionMode, setSelectionMode] = useState<'none' | 'manual' | 'all'>('none');
    // Track when we need to auto-select next job after state change
    const autoSelectNext = useRef<{ shouldSelect: boolean; previousJobId: number | null; previousJobIndex?: number }>({
        shouldSelect: false,
        previousJobId: null,
    });
    // Track if we are in the middle of an auto-selection
    const isAutoSelecting = useRef(false);
    // Track manual selection time to prevent stale URL from reverting state
    const lastManualSelectionTime = useRef<number>(0);

    // Keep a ref to allJobs to avoid recreating handleJobSelect when jobs change
    // This prevents the infinite loop/re-render issues in useViewer
    const allJobsRef = useRef(allJobs);
    useEffect(() => {
        allJobsRef.current = allJobs;
    }, [allJobs]);

    const handleJobSelect = useCallback((job: Job) => {
        lastManualSelectionTime.current = Date.now();
        setSelectedJob(job); 
        // Sync selection state with the clicked job
        setSelectedIds(new Set([job.id]));
        const selectedItems = allJobsRef.current.map((j,idx) => j.id === job.id ? idx:-1).filter(idx => idx!==-1)
        setSelectedIdxs(new Set(selectedItems));
        setSelectionMode('manual');
        // Update URL with jobId parameter - REMOVED to prevent unwanted filter resets
        // const newParams = new URLSearchParams(searchParams);
        // newParams.set('jobId', job.id.toString());
        // setSearchParams(newParams);
    }, [searchParams, setSearchParams, setSelectedIdxs]);

    useEffect(() => { // Reset selection when filters change (except page)
        setSelectionMode('none');
        setSelectedIds(new Set());
        setSelectedIdxs(new Set());
    }, [filters.search, filters.status, filters.not_status, filters.days_old, filters.salary, filters.order, filters.sql_filter]);

    // Auto-select next job after data refetch when a state change occurred
    useEffect(() => {
        if (!autoSelectNext.current.shouldSelect || !allJobs.length || !autoSelectNext.current.previousJobId) {
            return;
        }
        // Find the previous job in the new data
        const prevJobIdx = allJobs.findIndex(j => j.id === autoSelectNext.current.previousJobId);

        if (prevJobIdx === -1) {
            // Job was filtered out, select next available job
            if (allJobs.length > 0) {
                // Try to select the job at the same index, or the last job if we're past the end
                // Use stored index if available, fallback to selectedIdxs lookup
                let prevIdx = autoSelectNext.current.previousJobIndex;
                if (prevIdx === undefined) {
                    prevIdx = selectedIdxs?.values().next().value || 0;
                }
                
                const indexToSelect = Math.min(Math.max(0, prevIdx - 1), allJobs.length - 1);
                isAutoSelecting.current = true;
                lastManualSelectionTime.current = Date.now();
                const jobToSelect = allJobs[indexToSelect];
                setSelectedJob(jobToSelect);
                setSelectedIds(new Set([jobToSelect.id]));
            } else {
                // No jobs left in list
                setSelectedJob(null);
                setSelectedIds(new Set());
            }
        }
        // Reset the flag
        autoSelectNext.current = { shouldSelect: false, previousJobId: null, previousJobIndex: undefined };
    }, [allJobs, handleJobSelect, selectedIdxs]);

    useEffect(() => { // Handle jobId parameter separately
        if (isAutoSelecting.current) return;
        const jobIdParam = searchParams.get('jobId');
        if (jobIdParam) {
            const jobId = parseInt(jobIdParam, 10);
            if (!isNaN(jobId)) {
                // If we have jobId param, we strictly want to filter by this ID
                // ensuring all other filters are cleared.
                const sqlFilter = `id=${jobId}`;
                setFilters(prev => {
                    // If we are already strictly filtered by this ID, don't trigger update
                    if (prev.sql_filter === sqlFilter && 
                        !prev.search && 
                        !prev.status && 
                        !prev.days_old
                    ) return prev;
                    // Reset all filters, keeping only size if desired (or just defaults)
                    // We explicitly clear everything else.
                    return {
                        page: 1,
                        size: prev.size,
                        sql_filter: sqlFilter
                    };
                });
                // Check if we manually selected recently (within 500ms)
                // This prevents stale URL params from reverting the selection
                const isRecentManualSelection = Date.now() - lastManualSelectionTime.current < 500;
                if (isRecentManualSelection) {
                        // We have a recent manual selection that differs from URL (which is likely stale)
                        // Ignore this URL update
                        return;
                }
                // Try to find the job in the current list first
                const job = allJobs.find(j => j.id === jobId);
                if (job && selectedJob?.id !== job.id) {
                    setSelectedJob(job);
                    setSelectedIds(new Set([jobId]));
                }
                // Remove jobId from URL after processing to prevent sticking
                setSearchParams(prev => {
                    const newParams = new URLSearchParams(prev);
                    newParams.delete('jobId');
                    return newParams;
                });
            }
        }
    }, [searchParams, allJobs, selectedJob, setFilters, setSearchParams]);

    useEffect(() => { // Handle URL parameters on mount
        if (isAutoSelecting.current) {
            isAutoSelecting.current = false;
            return;
        }
        const idsParam = searchParams.get('ids');
        if (idsParam) {
            const ids = idsParam.split(',').map(id => parseInt(id, 10)).filter(id => !isNaN(id));
            if (ids.length > 0) {
                const sqlFilter = `id IN (${ids.join(',')})`;
                setFilters(prev => {
                    if (prev.sql_filter === sqlFilter) return prev;
                    return { ...prev, sql_filter: sqlFilter, page: 1, ignored: undefined, seen: undefined, applied: undefined, discarded: undefined, closed: undefined };
                });
                // Remove ids from URL so form works properly
                setSearchParams(prev => {
                    const newParams = new URLSearchParams(prev);
                    newParams.delete('ids');
                    return newParams;
                });
            }
        }
    }, [searchParams, setFilters, setSearchParams]);

    const navigateJob = useCallback((direction: 'next' | 'previous') => {
        if (!allJobs.length || !selectedJob) return;
        const currentIndex = allJobs.findIndex(j => j.id === selectedJob.id);
        if (currentIndex === -1) return;
        const nextIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1;
        if (nextIndex >= 0 && nextIndex < allJobs.length) {
            handleJobSelect(allJobs[nextIndex]);
        } else if (direction === 'next' && nextIndex >= allJobs.length && hasMorePages && onLoadMore) {
            onLoadMore();
        }
    }, [allJobs, selectedJob, handleJobSelect, hasMorePages, onLoadMore]);

    return {
        selectedJob,
        setSelectedJob,
        selectedIds,
        setSelectedIds,
        selectionMode,
        setSelectionMode,
        handleJobSelect,
        navigateJob,
        autoSelectNext, // Exposed for mutations
    };
};
