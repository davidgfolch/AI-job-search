import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { type Job, type JobListParams } from '../../api/jobs';

interface UseJobSelectionProps {
    allJobs: Job[];
    filters: JobListParams;
    setFilters: React.Dispatch<React.SetStateAction<JobListParams>>;
}

export const useJobSelection = ({ allJobs, filters, setFilters }: UseJobSelectionProps) => {
    const [searchParams, setSearchParams] = useSearchParams();
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
    const [selectedIdxs, setSelectedIdxs] = useState<Set<number>>(new Set());
    const [selectionMode, setSelectionMode] = useState<'none' | 'manual' | 'all'>('none');

    // Track when we need to auto-select next job after state change
    const autoSelectNext = useRef<{ shouldSelect: boolean; previousJobId: number | null }>({
        shouldSelect: false,
        previousJobId: null,
    });

    // Track if we are in the middle of an auto-selection
    const isAutoSelecting = useRef(false);
    // Track manual selection time to prevent stale URL from reverting state
    const lastManualSelectionTime = useRef<number>(0);

    const handleJobSelect = useCallback((job: Job) => {
        lastManualSelectionTime.current = Date.now();
        setSelectedJob(job); 
        // Sync selection state with the clicked job
        setSelectedIds(new Set([job.id]));
        const selectedItems = allJobs.map((j,idx) => j.id === job.id ? idx:-1).filter(idx => idx!==-1)
        setSelectedIdxs(new Set(selectedItems));
        setSelectionMode('manual');
        // Update URL with jobId parameter - REMOVED to prevent unwanted filter resets
        // const newParams = new URLSearchParams(searchParams);
        // newParams.set('jobId', job.id.toString());
        // setSearchParams(newParams);
    }, [searchParams, setSearchParams, setSelectedIdxs, allJobs]);

    // Reset selection when filters change (except page)
    useEffect(() => {
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
                const prevIdx: number = selectedIdxs?.values().next().value || 0;
                const indexToSelect = Math.min(prevIdx, allJobs.length - 1);
                isAutoSelecting.current = true;
                lastManualSelectionTime.current = Date.now();
                setSelectedJob(allJobs[indexToSelect]);
            } else {
                // No jobs left in list
                setSelectedJob(null);
            }
        }
        // Reset the flag
        autoSelectNext.current = { shouldSelect: false, previousJobId: null };
    }, [allJobs, handleJobSelect, selectedIdxs]);

    // Handle jobId parameter separately
    useEffect(() => {
        if (isAutoSelecting.current) {
            return;
        }
        
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
                    ) {
                        return prev;
                    }

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
                }

                // Remove jobId from URL after processing to prevent sticking
                setSearchParams(prev => {
                    const newParams = new URLSearchParams(prev);
                    newParams.delete('jobId');
                    // We also need to make sure we don't accidentally remove other things if we just reset them?
                    // Actually setFilters above handled the resetting of other params in the state.
                    // But the URL params (searchParams) might still have them if we don't clean them here?
                    // 'searchParams' comes from the URL. If the user navigated to ?jobId=123, then only jobId is there.
                    // If they navigated to ?search=foo&jobId=123, we want to clear the search from URL too?
                    // Yes, because we just cleared it in the filters state!
                    // So we should probably reset the URL to ONLY match the new state (which is empty except sql_filter)
                    // But sql_filter is not usually in URL unless explicitly set?
                    // Actually, let's just remove jobId. The filter state sync will handle the rest if wired up?
                    // Actually, if we just remove jobId, the other params (like search=foo) remain in URL?
                    // If they remain in URL, but our state says "empty", do we sync back to URL?
                    // Usually hooks sync State -> URL. 
                    // Let's assume removing jobId is the main request.
                    return newParams;
                });
            }
        }
    }, [searchParams, allJobs, selectedJob, setFilters, setSearchParams]);

    // Handle URL parameters on mount
    useEffect(() => {
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
        }
    }, [allJobs, selectedJob, handleJobSelect]);

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
