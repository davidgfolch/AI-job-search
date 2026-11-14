import { useEffect, useMemo, useState, useRef } from 'react';
import { useJobsData } from './useJobsData';
import { useJobSelection } from './useJobSelection';
import { useJobMutations, type TabType } from './useJobMutations';
import { useAppliedModal } from './useAppliedModal';
import { useModalityValues } from '../../common/hooks/useModalityValues';
import { type Job, jobsApi } from '../api/ViewerApi';
import { STATE_FIELDS } from '../constants';

export type { TabType };

export const useViewer = () => {
    const [activeTab, setActiveTab] = useState<TabType>('list');
    const { data: modalityValues = [] } = useModalityValues();
    const {
        filters, setFilters, allJobs, setAllJobs, isLoadingMore, data, isLoading, isPlaceholderData, error: queryError, handleLoadMore, setIsLoadingMore, hardRefresh, reloadCurrentPage
    } = useJobsData();
    const apiError = data?.error; // Error returned from API (e.g., database errors)
    const [dismissedApiErrors, setDismissedApiErrors] = useState<Set<string>>(new Set());
    const displayedApiError = apiError && !dismissedApiErrors.has(apiError) ? apiError : null;
    const hasMorePages = allJobs.length < (data?.total || 0);
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
    useEffect(() => {
        handleJobSelectRef.current = handleJobSelect;
    }, [handleJobSelect]);

    const {
        message, setMessage, confirmModal, handleJobUpdate, ignoreSelected, deleteSelected, deleteSingleJob, createMutation, bulkUpdateMutation
    } = useJobMutations({
        filters, allJobs, selectedJob, setSelectedJob, activeTab, autoSelectNext,
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

    const handleDismissMessage = () => {
        setMessage(null);
        if (displayedApiError) {
            setDismissedApiErrors(prev => new Set(prev).add(displayedApiError));
        }
    };

    // Clear dismissed API errors when filters change
    useEffect(() => {
        setDismissedApiErrors(new Set());
    }, [filters]);

    const { isModalOpen: isAppliedModalOpen, openModal: openAppliedModal, handleConfirm: handleAppliedConfirm, handleCancel: handleAppliedCancel } = useAppliedModal({
        selectedJob, allJobs, onJobUpdate: handleJobUpdate,
        onBulkUpdate: (ids: number[], update: Partial<Job>) => {
            // Set autoSelectNext for single job updates (e.g., from modal with selectedIds.size === 1)
            if (ids.length === 1 && activeTab === 'list') {
                const hasStateChange = STATE_FIELDS.some((field) => field in update);
                if (hasStateChange) {
                    const index = allJobs.findIndex(j => j.id === ids[0]);
                    autoSelectNext.current = {
                        shouldSelect: true,
                        previousJobId: ids[0],
                        previousJobIndex: index !== -1 ? index : undefined
                    };
                }
            }
            bulkUpdateMutation.mutate({ ids, update });
        },
        selectedIds, selectionMode,
    });

    const [shouldSelectFirst, setShouldSelectFirst] = useState(false);
    const [creationSessionId, setCreationSessionId] = useState(0);
    const [duplicatedJob, setDuplicatedJob] = useState<Job | null>(null);
    const autoSelectAllAfterLoad = useRef(false);

    const openDuplicatedJob = async (id: number) => {
        try { setDuplicatedJob(await jobsApi.getJob(id)); } 
        catch (e) { console.error("Failed to load duplicated job", e); }
    };

    const configKey = useMemo(() =>
        // `auto_select_all` is selection behaviour, not a job filter: excluding it keeps toggling the pill from
        // clearing the list, and the dedicated effect below arms the auto-selection instead.
        JSON.stringify(Object.fromEntries(Object.entries(filters).filter(([key]) => key !== 'page' && key !== 'auto_select_all'))),
    [filters]);

    useEffect(() => {
        setAllJobs([]);
    }, [configKey, setAllJobs]);

    useEffect(() => {
        if (data?.items && data.page === (filters.page || 1) && !isPlaceholderData) {
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
    }, [data, filters.page, isPlaceholderData, setAllJobs, setIsLoadingMore]);

    // Arm the auto-selection whenever a filter set with `auto_select_all` is applied (config load, pill toggle or
    // a filter change). It is disarmed once the selection is applied, so manually deselecting rows is respected
    // until the next configuration/filter change.
    useEffect(() => {
        autoSelectAllAfterLoad.current = filters.auto_select_all === true;
    }, [filters.auto_select_all, configKey]);

    useEffect(() => {
        if (!autoSelectAllAfterLoad.current || isPlaceholderData) return;
        if ((filters.page || 1) !== 1 || data?.page !== 1 || !data.items?.length) return;
        autoSelectAllAfterLoad.current = false;
        if (selectionMode !== 'all') setSelectionMode('all');
    }, [data, filters.page, filters.auto_select_all, isPlaceholderData, configKey, selectionMode, setSelectionMode]);

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
        state: { filters, allJobs, selectedJob, activeTab, message, data, selectedIds, selectionMode, confirmModal, activeConfigName, creationSessionId, duplicatedJob, modalityValues,
            appliedModal: { isOpen: isAppliedModalOpen, onConfirm: handleAppliedConfirm, onCancel: handleAppliedCancel } },
        status: { isLoading: (isLoading || isPlaceholderData) && (filters.page || 1) === 1, isLoadingMore, error: queryError, apiError: displayedApiError, hasNext, hasPrevious },
        actions: {
            setFilters, setActiveTab, setMessage, selectJob: handleJobSelect, updateJob: handleJobUpdate,
            ignoreJob: () => handleJobUpdate({ ignored: true }), seenJob: () => handleJobUpdate({ seen: true }),
            appliedJob: openAppliedModal, discardedJob: () => handleJobUpdate({ discarded: true }), closedJob: () => handleJobUpdate({ closed: true }),
            deleteJob: deleteSingleJob, nextJob: () => navigateJob('next'), previousJob: () => navigateJob('previous'), loadMore: handleLoadMore,
            toggleSelectJob: (id: number) => {
                if (selectionMode === 'all') {
                    // Deselecting one row while all are selected: switch to manual with every loaded job except this one
                    const newSelected = new Set<number>();
                    for (const job of allJobs) {
                        if (job.id !== id) newSelected.add(job.id);
                    }
                    setSelectionMode('manual');
                    setSelectedIds(newSelected);
                    const job = allJobs.find(j => j.id === id);
                    if (job) setSelectedJob(job);
                    return;
                }
                const newSelected = new Set(selectedIds);
                if (newSelected.has(id)) {
                    newSelected.delete(id);
                    if (newSelected.size === 0) {
                        setSelectionMode('none');
                    }
                } else {
                    newSelected.add(id);
                    setSelectionMode('manual');
                    const job = allJobs.find(j => j.id === id);
                    if (job) setSelectedJob(job);
                }
                setSelectedIds(newSelected);
            },
            toggleSelectAll: () => selectionMode === 'all' ? (setSelectionMode('none'), setSelectedIds(new Set())) : setSelectionMode('all'),
            ignoreSelected, deleteSelected, setActiveConfigName, closeConfirmModal: () => confirmModal.close(), dismissMessage: handleDismissMessage,
            createJob: async (data: Partial<Job>) => {
                await createMutation.mutateAsync(data);
                setActiveTab('list'); setFilters(f => ({ ...f, page: 1 })); setCreationSessionId(p => p + 1);
            },
            refreshJobs: async () => filters.page !== 1 ? (setShouldSelectFirst(true), setFilters(f => ({ ...f, page: 1 }))) : (setShouldSelectFirst(true), await hardRefresh()),
            // Re-applying the filter configuration that is already active leaves the query key untouched, so the
            // list would keep the jobs it already has. Refetch the page in place instead, keeping the selection.
            reloadJobList: reloadCurrentPage,
            openDuplicatedJob, closeDuplicatedJob: () => setDuplicatedJob(null), closeSelectedJob: () => { setSelectedJob(null); setSelectionMode('none'); setSelectedIds(new Set()); },
        },
    };
};
