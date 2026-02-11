export interface WatcherResult {
    total: number;
    newItems: number;
}

export interface UseFilterWatcherProps {
    savedConfigs: Array<{
        id?: number;
        name: string;
        watched?: boolean;
    }>;
}

export const POLLING_INTERVAL = 5 * 60 * 1000; // 5 minutes
