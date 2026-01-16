import { useEffect, useState } from 'react';
import { useJobsData } from './viewer/useJobsData';
import { useJobSelection } from './viewer/useJobSelection';
import { useJobMutations, type TabType } from './viewer/useJobMutations';
import { useJobUpdates } from './viewer/useJobUpdates';
import type { Job } from '../api/jobs';

export type { TabType };

export const useViewer = () => {
    const [activeTab, setActiveTab] = useState<TabType>('list');

    const {
        filters, setFilters, allJobs, setAllJobs, isLoadingMore, data, isLoading, error, handleLoadMore, setIsLoadingMore, hardRefresh
    } = useJobsData();

    const {
        selectedJob, setSelectedJob, selectedIds, setSelectedIds,
        selectionMode, setSelectionMode, handleJobSelect, navigateJob, autoSelectNext
    } = useJobSelection({ allJobs, filters, setFilters });

    const [knownJobIds, setKnownJobIds] = useState<Set<number>>(new Set());
    const { hasNewJobs, newJobsCount } = useJobUpdates(filters, knownJobIds);

    const [activeConfigName, setActiveConfigName] = useState<string>('');

    const {
        message, setMessage, confirmModal, handleJobUpdate, ignoreSelected, deleteSelected, deleteSingleJob, createMutation
    } = useJobMutations({
        filters, selectedJob, setSelectedJob, activeTab, autoSelectNext,
        selectedIds, setSelectedIds, selectionMode, setSelectionMode,
        onJobUpdated: (updatedJob) => {
            setAllJobs(jobs => {
                // Remove job if no longer matches state filters
                if ((filters.ignored !== updatedJob.ignored) || 
                    (filters.seen !== updatedJob.seen) || 
                    (filters.applied !== updatedJob.applied) || 
                    (filters.discarded !== updatedJob.discarded) ||
                    (filters.closed !== updatedJob.closed)) {
                    return jobs.filter(j => j.id !== updatedJob.id);
                }
                return jobs.map(j => j.id === updatedJob.id ? updatedJob : j);
            });
        },
        onJobsDeleted: (ids) => {
            if (ids === 'all') {
                setAllJobs([]);
                setFilters(f => ({ ...f, page: 1 }));
            } else {
                setAllJobs(jobs => jobs.filter(j => !ids.includes(j.id)));
            }
        }
    });

    const [shouldSelectFirst, setShouldSelectFirst] = useState(false);
    const [creationSessionId, setCreationSessionId] = useState(0);

    // Update allJobs when data changes
    useEffect(() => {
        if (data?.items) {
            setAllJobs(jobs => {
                if (filters.page === 1) { // Reset on first page (new search/filter)
                    return data.items;
                } else { // Append on subsequent pages
                    const newItems = data.items.filter(item => !jobs.some(p => p.id === item.id));
                    return [...jobs, ...newItems];
                }
            });
            
            // Update knownJobIds to include all jobs we've seen in this session
            setKnownJobIds(prev => {
                const next = new Set(prev);
                data.items.forEach(j => next.add(j.id));
                return next;
            });
            
            setIsLoadingMore(false);
        }
    }, [data, filters.page, setAllJobs, setIsLoadingMore]);

    // Handle initial selection purely based on flag
    useEffect(() => {
        if (shouldSelectFirst && data?.items && data.items.length > 0) {
            // We use a timeout to avoid immediate state clash or loop, though splitting effects should be enough
            handleJobSelect(data.items[0]);
            setShouldSelectFirst(false);
        }
    }, [shouldSelectFirst, data, handleJobSelect]);
    
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
            activeConfigName,
            hasNewJobs,
            newJobsCount,
            creationSessionId,
        },
        status: {
            isLoading: isLoading && (filters.page || 1) === 1,
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
            deleteJob: deleteSingleJob,
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
            ignoreSelected,
            deleteSelected,
            setActiveConfigName,
            closeConfirmModal: () => confirmModal.close(),
            createJob: async (data: Partial<Job>) => {
                await createMutation.mutateAsync(data);
                // Switch to list and refresh to show the new job
                setActiveTab('list');
                setFilters(f => ({ ...f, page: 1 })); // Refresh list
                setCreationSessionId(prev => prev + 1);
            },
            refreshJobs: async () => {
                if (filters.page !== 1) {
                    setShouldSelectFirst(true);
                    setFilters(f => ({ ...f, page: 1 }));
                } else {
                    setShouldSelectFirst(true);
                    await hardRefresh();
                }
            },
        },
    };
};
