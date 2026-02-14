import { useEffect, useState, useRef } from 'react';
import { useJobsData } from './useJobsData';
import { useJobSelection } from './useJobSelection';
import { useJobMutations, type TabType } from './useJobMutations';
import { useAppliedModal } from './useAppliedModal';
import { type Job, jobsApi } from '../api/ViewerApi';

export type { TabType };

export const useViewer = () => {
    const [activeTab, setActiveTab] = useState<TabType>('list');
    const {
        filters, setFilters, allJobs, setAllJobs, isLoadingMore, data, isLoading, error, handleLoadMore, setIsLoadingMore, hardRefresh
    } = useJobsData();
    const hasMorePages = allJobs.length < (data?.total || 0) - 1;
    const shouldAutoSelectNextPage = useRef(false);
    const handleLoadMoreWithAutoSelect = () => {
        shouldAutoSelectNextPage.current = true;
        handleLoadMore();
    };
    const {
        selectedJob, setSelectedJob, selectedIds, setSelectedIds,
        selectionMode, setSelectionMode, handleJobSelect, navigateJob, autoSelectNext
    } = useJobSelection({ allJobs, filters, setFilters, onLoadMore: handleLoadMoreWithAutoSelect, hasMorePages });
    const [activeConfigName, setActiveConfigName] = useState<string>('');

    // Keep a ref to handleJobSelect to avoid recreating effect when it changes
    const handleJobSelectRef = useRef(handleJobSelect);
    handleJobSelectRef.current = handleJobSelect;

    const {
        message, setMessage, confirmModal, handleJobUpdate, ignoreSelected, deleteSelected, deleteSingleJob, createMutation, bulkUpdateMutation
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
        },
        activeConfigName,
    });

    const { // Applied modal integration
        isModalOpen: isAppliedModalOpen,
        openModal: openAppliedModal,
        handleConfirm: handleAppliedConfirm,
        handleCancel: handleAppliedCancel,
    } = useAppliedModal({
        selectedJob,
        allJobs,
        onJobUpdate: handleJobUpdate,
        onBulkUpdate: (ids: number[], update: Partial<Job>) => {
            bulkUpdateMutation.mutate({ ids, update });
        },
        selectedIds,
        selectionMode,
    });

    const [shouldSelectFirst, setShouldSelectFirst] = useState(false);
    const [creationSessionId, setCreationSessionId] = useState(0);
    const [duplicatedJob, setDuplicatedJob] = useState<Job | null>(null);

    const openDuplicatedJob = async (id: number) => {
        try {
            const job = await jobsApi.getJob(id);
            setDuplicatedJob(job);
        } catch (e) {
            console.error("Failed to load duplicated job", e);
        }
    };

    const closeDuplicatedJob = () => {
        setDuplicatedJob(null);
    };

    useEffect(() => { // Update allJobs when data changes
        if (data?.items) {
            if (data.page !== (filters.page || 1)) return;

            setAllJobs(jobs => {
                if (filters.page === 1) { // Reset on first page (new search/filter)
                    return data.items;
                } else { // Append on subsequent pages
                    const newItems = data.items.filter(item => !jobs.some(p => p.id === item.id));
                    if (newItems.length === 0) {
                        return jobs;
                    }
                    if (shouldAutoSelectNextPage.current) {
                        setTimeout(() => {
                            handleJobSelectRef.current(newItems[0]);
                            shouldAutoSelectNextPage.current = false;
                        }, 0);
                    }
                    return [...jobs, ...newItems];
                }
            });
            setIsLoadingMore(false);
        }
    }, [data, filters.page, setAllJobs, setIsLoadingMore]);

    useEffect(() => { // Handle initial selection purely based on flag
        if (shouldSelectFirst && data?.items && data.items.length > 0) {
            // We use a timeout to avoid immediate state clash or loop, though splitting effects should be enough
            handleJobSelectRef.current(data.items[0]);
            setShouldSelectFirst(false);
        }
    }, [shouldSelectFirst, data]);
    
    // Calculate navigation state
    const selectedIndex = allJobs.findIndex(j => j.id === selectedJob?.id) ?? -1;
    const hasNext = (selectedIndex >= 0 && selectedIndex < allJobs.length - 1) || hasMorePages;
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
            creationSessionId,
            duplicatedJob,
            appliedModal: {
                isOpen: isAppliedModalOpen,
                onConfirm: handleAppliedConfirm,
                onCancel: handleAppliedCancel,
            },
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
            appliedJob: openAppliedModal,
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
            openDuplicatedJob,
            closeDuplicatedJob,
        },
    };
};
