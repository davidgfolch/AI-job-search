import { useQuery } from '@tanstack/react-query';
import { jobsApi } from '../api/ViewerApi';
import { type JobListParams } from '../api/ViewerApi';

export const useJobUpdates = (filters: JobListParams, knownJobIds: Set<number>) => {
    // Exclude page from queryKey so that pagination doesn't reset the polling timer
    // We want the check to run every 5 minutes regardless of which page the user is on
    const { page, ...filtersWithoutPage } = filters;
    
    const { data } = useQuery({
        queryKey: ['jobUpdates', filtersWithoutPage],
        queryFn: () => jobsApi.getJobs({ ...filters, page: 1 }),
        refetchInterval: 1 * 60 * 1000,
        refetchIntervalInBackground: true,
    });

    const newJobsCount = data?.items.filter(job => !knownJobIds.has(job.id)).length ?? 0;
    const hasNewJobs = newJobsCount > 0;

    return { hasNewJobs, newJobsCount };
};
