import { useEffect, useState } from 'react';
import { useJobsData } from './viewer/useJobsData';
import { useJobSelection } from './viewer/useJobSelection';
import { useJobMutations, type TabType } from './viewer/useJobMutations';

export type { TabType };

export const useViewer = () => {
    const [activeTab, setActiveTab] = useState<TabType>('list');

    const {
        filters, setFilters, allJobs, setAllJobs, isLoadingMore, data, isLoading, error, handleLoadMore, setIsLoadingMore
    } = useJobsData();

    const {
        selectedJob, setSelectedJob, selectedIds, setSelectedIds,
        selectionMode, setSelectionMode, handleJobSelect, navigateJob, autoSelectNext
    } = useJobSelection({ allJobs, filters, setFilters });

    const {
        message, setMessage, confirmModal, setConfirmModal, handleJobUpdate, ignoreSelected
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
            setAllJobs(jobs => jobs.filter(j => !ids.includes(j.id)));
        }
    });

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
            setIsLoadingMore(false);
        }
    }, [data, filters.page, setAllJobs, setIsLoadingMore]);
    
    

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
            closeConfirmModal: () => setConfirmModal(prev => ({ ...prev, isOpen: false })),
        },
    };
};
