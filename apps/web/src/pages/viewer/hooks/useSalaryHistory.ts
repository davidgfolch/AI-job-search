import { useQuery } from '@tanstack/react-query';
import { jobsApi, type SalaryHistoryEntry } from '../api/ViewerApi';

export function useSalaryHistory(jobId: number | undefined) {
    return useQuery<SalaryHistoryEntry[]>({
        queryKey: ['salaryHistory', jobId],
        queryFn: () => jobsApi.getJobHistory(jobId!),
        enabled: !!jobId,
        staleTime: 2 * 60 * 1000,
    });
}

export function useCompanySalaryHistory(company: string | undefined | null) {
    return useQuery<SalaryHistoryEntry[]>({
        queryKey: ['companySalaryHistory', company],
        queryFn: () => jobsApi.getCompanyHistory(company!),
        enabled: !!company,
        staleTime: 10 * 60 * 1000,
        gcTime: 30 * 60 * 1000,
    });
}
