import { useQuery } from '@tanstack/react-query';
import { jobsApi, type JobListParams } from '../../api/jobs';

export const useJobUpdates = (filters: JobListParams, knownJobIds: Set<number>) => {
    const { data } = useQuery({
        queryKey: ['jobUpdates', filters],
        queryFn: () => jobsApi.getJobs({ ...filters, page: 1 }),
        refetchInterval: 5 * 60 * 1000,
    });

    const newJobsCount = data?.items.filter(job => !knownJobIds.has(job.id)).length ?? 0;
    const hasNewJobs = newJobsCount > 0;

    return { hasNewJobs, newJobsCount };
};
