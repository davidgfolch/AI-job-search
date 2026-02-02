import { useState, useEffect, useRef, useCallback } from 'react';
import type { FilterConfig } from './useFilterConfigurations';
import { jobsApi } from '../../../api/ViewerApi';

export interface WatcherResult {
    total: number;
    newItems: number;
}

export interface UseFilterWatcherProps {
    savedConfigs: FilterConfig[];
}

const POLLING_INTERVAL = 5 * 60 * 1000; // 5 minutes

export function useFilterWatcher({ savedConfigs }: UseFilterWatcherProps) {
    const [isWatching, setIsWatching] = useState(false);
    const [results, setResults] = useState<Record<string, WatcherResult>>({});
    const [lastCheckTime, setLastCheckTime] = useState<Date | null>(null);
    const [startTime, setStartTime] = useState<Date | null>(null);
    const configStartTimes = useRef<Record<string, Date>>({});
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const savedConfigsRef = useRef(savedConfigs);
    const isMounted = useRef(true);

    useEffect(() => {
        savedConfigsRef.current = savedConfigs;
    }, [savedConfigs]);

    useEffect(() => {
        isMounted.current = true;
        return () => {
            isMounted.current = false;
        };
    }, []);

    const checkItems = useCallback(async () => {
        if (!startTime) return;

        const newResults: Record<string, WatcherResult> = {};
        
        const configsToCheck = savedConfigsRef.current;

        for (const config of configsToCheck) {
            try {
                // Determine the created_after for this specific config
                // Use individual config start time if available, otherwise global start time
                const configStartTime = configStartTimes.current[config.name] || startTime;
                const createdAfterIso = configStartTime.toISOString();

                // Get total count
                const totalResponse = await jobsApi.getJobs({ ...config.filters, page: 1, size: 1 });
                
                // Get new items count
                const newItemsResponse = await jobsApi.getJobs({ 
                    ...config.filters, 
                    page: 1, 
                    size: 1,
                    // casting to any because created_after is not yet defined in JobListParams interface
                    // @ts-ignore
                    created_after: createdAfterIso 
                });

                if (isMounted.current) {
                    newResults[config.name] = {
                        total: totalResponse.total,
                        newItems: newItemsResponse.total
                    };
                }
            } catch (error) {
                console.error(`Error checking config ${config.name}:`, error);
            }
        }

        if (isMounted.current) {
            setResults(newResults);
            setLastCheckTime(new Date());
        }
    }, [startTime]);

    const startWatching = () => {
        setIsWatching(true);
        const now = new Date();
        setStartTime(now);
        setLastCheckTime(now);
        setResults({});
        configStartTimes.current = {}; // Reset all individual times
    };

    const stopWatching = () => {
        setIsWatching(false);
        setStartTime(null);
        setLastCheckTime(null);
        configStartTimes.current = {};
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    };

    const resetWatcher = (configName: string) => {
        const now = new Date();
        configStartTimes.current[configName] = now;
        
        // Optimistically reset count to 0 for this config in results
        setResults(prev => {
            const current = prev[configName];
            if (!current) return prev;
            return {
                ...prev,
                [configName]: { ...current, newItems: 0 }
            };
        });
    };

    // Effect to handle polling
    useEffect(() => {
        if (isWatching && startTime) {
            // Immediate check when starting (or rather when startTime is set)
            checkItems();

            intervalRef.current = setInterval(checkItems, POLLING_INTERVAL);
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [isWatching, startTime, checkItems]);

    return {
        isWatching,
        results,
        lastCheckTime,
        startWatching,
        stopWatching,
        resetWatcher
    };
}
