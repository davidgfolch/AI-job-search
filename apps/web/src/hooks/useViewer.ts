import { useState } from 'react';
import { useJobsData } from './viewer/useJobsData';
import { useJobSelection } from './viewer/useJobSelection';
import { useJobMutations, type TabType } from './viewer/useJobMutations';

export type { TabType };

export const useViewer = () => {
    const [activeTab, setActiveTab] = useState<TabType>('list');

    const {
        filters, setFilters, allJobs, isLoadingMore, data, isLoading, error, handleLoadMore
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
            setAllJobs(prev => {
                // If the job no longer matches boolean filters (e.g. marked as seen when filtering by unseen), remove it
                let shouldRemove = false;
                if (filters.seen === false && updatedJob.seen) shouldRemove = true;
                if (filters.ignored === false && updatedJob.ignored) shouldRemove = true;
                if (filters.discarded === false && updatedJob.discarded) shouldRemove = true;

                if (shouldRemove) {
                    return prev.filter(j => j.id !== updatedJob.id);
                }
                return prev.map(j => j.id === updatedJob.id ? updatedJob : j);
            });
        },
        onJobsDeleted: (ids) => {
            setAllJobs(prev => prev.filter(j => !ids.includes(j.id)));
        }
    });

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
