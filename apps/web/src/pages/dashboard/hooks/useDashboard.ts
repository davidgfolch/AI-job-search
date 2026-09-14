import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/DashboardApi';

const REFRESH_INTERVAL_MS = 30000;

export const useDashboard = () => {
    return useQuery({
        queryKey: ['dashboard'],
        queryFn: () => dashboardApi.getServicesStatus(),
        refetchInterval: REFRESH_INTERVAL_MS,
    });
};
