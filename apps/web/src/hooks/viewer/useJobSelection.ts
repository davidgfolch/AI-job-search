import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { jobsApi, type Job, type JobListParams } from '../../api/jobs';

interface UseJobSelectionProps {
    allJobs: Job[];
    filters: JobListParams;
    setFilters: React.Dispatch<React.SetStateAction<JobListParams>>;
}

export const useJobSelection = ({ allJobs, filters, setFilters }: UseJobSelectionProps) => {
    const [searchParams, setSearchParams] = useSearchParams();
    const [selectedJob, setSelectedJob] = useState<Job | null>(null);
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
    const [selectionMode, setSelectionMode] = useState<'none' | 'manual' | 'all'>('none');

    // Track when we need to auto-select next job after state change
    const autoSelectNext = useRef<{ shouldSelect: boolean; previousJobId: number | null }>({
        shouldSelect: false,
        previousJobId: null,
    });

    // Track if we are in the middle of an auto-selection
    const isAutoSelecting = useRef(false);

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

    // Reset selection when filters change (except page)
    useEffect(() => {
        setSelectionMode('none');
        setSelectedIds(new Set());
    }, [filters.search, filters.status, filters.not_status, filters.days_old, filters.salary, filters.order, filters.sql_filter]);

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
    }, [searchParams, allJobs, setFilters, setSearchParams]);

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
