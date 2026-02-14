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

    const handleJobSelectRef = useRef(handleJobSelect);
    handleJobSelectRef.current = handleJobSelect;

    const {
        message, setMessage, confirmModal, handleJobUpdate, ignoreSelected, deleteSelected, deleteSingleJob, createMutation, bulkUpdateMutation
    } = useJobMutations({
        filters, selectedJob, setSelectedJob, activeTab, autoSelectNext,
        selectedIds, setSelectedIds, selectionMode, setSelectionMode,
        onJobUpdated: (updatedJob) => {
            setAllJobs(jobs => {
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

    const { isModalOpen: isAppliedModalOpen, openModal: openAppliedModal, handleConfirm: handleAppliedConfirm, handleCancel: handleAppliedCancel } = useAppliedModal({
        selectedJob, allJobs, onJobUpdate: handleJobUpdate,
        onBulkUpdate: (ids: number[], update: Partial<Job>) => bulkUpdateMutation.mutate({ ids, update }),
        selectedIds, selectionMode,
    });

    const [shouldSelectFirst, setShouldSelectFirst] = useState(false);
    const [creationSessionId, setCreationSessionId] = useState(0);
    const [duplicatedJob, setDuplicatedJob] = useState<Job | null>(null);

    const openDuplicatedJob = async (id: number) => {
        try { setDuplicatedJob(await jobsApi.getJob(id)); } 
        catch (e) { console.error("Failed to load duplicated job", e); }
    };

    useEffect(() => {
        if (data?.items && data.page === (filters.page || 1)) {
            setAllJobs(jobs => {
                if (filters.page === 1) return data.items;
                const newItems = data.items.filter(item => !jobs.some(p => p.id === item.id));
                if (newItems.length === 0) return jobs;
                if (shouldAutoSelectNextPage.current) {
                    setTimeout(() => { handleJobSelectRef.current(newItems[0]); shouldAutoSelectNextPage.current = false; }, 0);
                }
                return [...jobs, ...newItems];
            });
            setIsLoadingMore(false);
        }
    }, [data, filters.page, setAllJobs, setIsLoadingMore]);

    useEffect(() => {
        if (shouldSelectFirst && data?.items?.length) {
            handleJobSelectRef.current(data.items[0]);
            setShouldSelectFirst(false);
        }
    }, [shouldSelectFirst, data]);

    const selectedIndex = allJobs.findIndex(j => j.id === selectedJob?.id) ?? -1;
    const hasNext = (selectedIndex >= 0 && selectedIndex < allJobs.length - 1) || hasMorePages;
    const hasPrevious = selectedIndex > 0;

    return {
        state: { filters, allJobs, selectedJob, activeTab, message, data, selectedIds, selectionMode, confirmModal, activeConfigName, creationSessionId, duplicatedJob,
            appliedModal: { isOpen: isAppliedModalOpen, onConfirm: handleAppliedConfirm, onCancel: handleAppliedCancel } },
        status: { isLoading: isLoading && (filters.page || 1) === 1, isLoadingMore, error, hasNext, hasPrevious },
        actions: {
            setFilters, setActiveTab, setMessage, selectJob: handleJobSelect, updateJob: handleJobUpdate,
            ignoreJob: () => handleJobUpdate({ ignored: true }), seenJob: () => handleJobUpdate({ seen: true }),
            appliedJob: openAppliedModal, discardedJob: () => handleJobUpdate({ discarded: true }), closedJob: () => handleJobUpdate({ closed: true }),
            deleteJob: deleteSingleJob, nextJob: () => navigateJob('next'), previousJob: () => navigateJob('previous'), loadMore: handleLoadMore,
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
            toggleSelectAll: () => selectionMode === 'all' ? (setSelectionMode('none'), setSelectedIds(new Set())) : setSelectionMode('all'),
            ignoreSelected, deleteSelected, setActiveConfigName, closeConfirmModal: () => confirmModal.close(),
            createJob: async (data: Partial<Job>) => {
                await createMutation.mutateAsync(data);
                setActiveTab('list'); setFilters(f => ({ ...f, page: 1 })); setCreationSessionId(p => p + 1);
            },
            refreshJobs: async () => filters.page !== 1 ? (setShouldSelectFirst(true), setFilters(f => ({ ...f, page: 1 }))) : (setShouldSelectFirst(true), await hardRefresh()),
            openDuplicatedJob, closeDuplicatedJob: () => setDuplicatedJob(null),
        },
    };
};
