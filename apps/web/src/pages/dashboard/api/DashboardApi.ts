import apiClient from '../../common/api/ApiClient';

export interface ServiceError {
    timestamp: string;
    event: string;
    level: string;
    message: string;
}

export interface OllamaError {
    timestamp: string;
    event: string;
    module: string;
    message: string;
}

export interface ServiceMetrics {
    pendingJobs: number;
    processed: number;
    succeeded: number;
    failed: number;
    lastError: string | null;
    lastErrorAt: string | null;
}

export interface ServiceStatus {
    name: string;
    displayName: string;
    status: 'running' | 'stopped' | 'error';
    lastActivity: string | null;
    usesOllama: boolean;
    metrics: ServiceMetrics;
    recentErrors: ServiceError[];
}

export interface OllamaStatus {
    reachable: boolean;
    recentErrors: OllamaError[];
}

export interface DashboardData {
    services: ServiceStatus[];
    ollama: OllamaStatus;
    timestamp: string;
}

export const dashboardApi = {
    getServicesStatus: async (): Promise<DashboardData> => {
        const response = await apiClient.get<DashboardData>('/dashboard/services');
        return response.data;
    },
};
