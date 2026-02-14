import { useState, useCallback, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import { jobsApi, type Job, type JobListParams } from '../api/ViewerApi';
import { DEFAULT_FILTERS } from '../constants';

export const useJobsData = () => {
    const [searchParams] = useSearchParams();

    const getInitialFilters = (): JobListParams => {
        const idsParam = searchParams.get('ids');
        if (idsParam) {
            const ids = idsParam.split(',').map(n => parseInt(n, 10)).filter(n => !isNaN(n));
            if (ids.length > 0) {
                return {
                    ...DEFAULT_FILTERS,
                    ids,
                    // When showing specific IDs, disable default filters to ensure they are visible
                    ai_enriched: undefined,
                    ignored: undefined,
                    seen: undefined,
                    applied: undefined,
                    discarded: undefined,
                    closed: undefined,
                    page: 1,
                };
            }
        }
        return DEFAULT_FILTERS;
    };

    const [filters, setFilters] = useState<JobListParams>(getInitialFilters);
    const [allJobs, setAllJobs] = useState<Job[]>([]);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const requestedPages = useRef(new Set<number>());

    const queryClient = useQueryClient();

    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ['jobs', filters],
        queryFn: () => jobsApi.getJobs(filters),
        placeholderData: keepPreviousData,
        staleTime: 1000 * 30, // 30 seconds
    });

    // Reset requested pages when starting a new search (page 1)
    useEffect(() => {
        if (filters.page === 1) {
            requestedPages.current.clear();
        }
    }, [filters.page]);

    const hardRefresh = useCallback(async () => {
        requestedPages.current.clear();
        await Promise.all([
            queryClient.resetQueries({ queryKey: ['jobs'] }),
            queryClient.resetQueries({ queryKey: ['jobUpdates'] })
        ]);
    }, [queryClient]);

    const handleLoadMore = useCallback(() => {
        const nextPage = (filters.page || 1) + 1;
        if (!isLoadingMore && !isLoading && allJobs.length < (data?.total || 0) && !requestedPages.current.has(nextPage)) {
            requestedPages.current.add(nextPage);
            setIsLoadingMore(true);
            setFilters(prev => ({ ...prev, page: nextPage }));
        }
    }, [isLoadingMore, isLoading, allJobs.length, data?.total, filters.page]);

    return {
        filters,
        setFilters,
        allJobs,
        setAllJobs,
        isLoadingMore,
        data,
        isLoading,
        error,
        handleLoadMore,
        setIsLoadingMore,
        refetch,
        hardRefresh
    };
};
