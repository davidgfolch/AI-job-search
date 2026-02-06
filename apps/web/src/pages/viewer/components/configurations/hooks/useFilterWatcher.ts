import { useState, useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { FilterConfig } from './useFilterConfigurations';
import { jobsApi } from '../../../api/ViewerApi';
import { notificationService } from '../../../../../common/services/NotificationService';

export interface WatcherResult {
    total: number;
    newItems: number;
}

export interface UseFilterWatcherProps {
    savedConfigs: FilterConfig[];
}

export const POLLING_INTERVAL = 5 * 60 * 1000; // 5 minutes

export function useFilterWatcher({ savedConfigs }: UseFilterWatcherProps) {
    const [isWatching, setIsWatching] = useState(true);
    const [results, setResults] = useState<Record<string, WatcherResult>>({});
    const [lastCheckTime, setLastCheckTime] = useState<Date | null>(new Date());
    const [startTime, setStartTime] = useState<Date | null>(new Date());
    const configStartTimes = useRef<Record<string, Date>>({});
    const notifiedCountsRef = useRef<Record<string, number>>({});
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const savedConfigsRef = useRef(savedConfigs);
    const isMounted = useRef(true);

    const queryClient = useQueryClient();

    useEffect(() => {
        if (isWatching) {
            notificationService.requestPermission();
        }
    }, []);

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
        const configIdsWithNames: Array<{ id: number; name: string }> = [];
        for (const config of configsToCheck) {
            if (!config.id) {
                console.warn(`Config ${config.name} has no ID, skipping watcher stats`);
                continue;
            }
            configIdsWithNames.push({ id: config.id, name: config.name });
        }
        if (configIdsWithNames.length === 0) return;
        try {
            const cutoffMap: Record<number, string> = {};
            configIdsWithNames.forEach(c => {
                const configStartTime = configStartTimes.current[c.name] || startTime;
                cutoffMap[c.id] = new Date(configStartTime).toISOString();
            });
            const statsMap = await jobsApi.getWatcherStats(cutoffMap);
            if (isMounted.current) {
                for (const { id, name } of configIdsWithNames) {
                    const stats = statsMap[id];
                    if (stats) {
                        newResults[name] = {
                            total: stats.total,
                            newItems: stats.new_items
                        };
                    }
                }
            }
        } catch (error) {
            console.error('Error checking watcher stats:', error);
        }
        const notificationAggregator: string[] = [];
        let totalNewJobs = 0;
        if (isMounted.current) {
            setResults(newResults);
            setLastCheckTime(new Date());
            // Check for notifications
            Object.entries(newResults).forEach(([name, result]) => {
                const prevCount = notifiedCountsRef.current[name] || 0;
                // If we found more items than before
                if (result.newItems > prevCount) {
                    // Update the tracker
                    notifiedCountsRef.current[name] = result.newItems;
                    // Check if this config has notifications enabled
                    const config = configsToCheck.find(c => c.name === name);
                    if (config && config.notify) {
                        notificationAggregator.push(`${name} (${result.newItems})`);
                        totalNewJobs += result.newItems;
                    }
                }
            });
            if (notificationAggregator.length > 0) {
                 const summary = notificationAggregator.join(', ');
                 notificationService.notify(`New jobs found`, {
                     body: summary,
                 });
            }
        }
    }, [startTime]);

    // Track whether we have any configs with IDs
    // This will cause the main effect to re-run when configs with IDs become available
    const hasConfigsWithIds = savedConfigs.some(c => c.id);
    const startWatching = () => {
        notificationService.requestPermission();
        setIsWatching(true);
        const now = new Date();
        setStartTime(now);
        setLastCheckTime(now);
        setResults({});
        configStartTimes.current = {}; // Reset all individual times
        notifiedCountsRef.current = {};
    };
    const stopWatching = () => {
        setIsWatching(false);
        setStartTime(null);
        setLastCheckTime(null);
        configStartTimes.current = {};
        notifiedCountsRef.current = {};
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    };
    const resetWatcher = (configName: string) => {
        const now = new Date();
        configStartTimes.current[configName] = now;
        notifiedCountsRef.current[configName] = 0;
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

    // Effect to handle polling and query updates
    useEffect(() => {
        if (isWatching && startTime && hasConfigsWithIds) {
            // Immediate check when starting (or rather when startTime is set)
            checkItems();
            intervalRef.current = setInterval(checkItems, POLLING_INTERVAL);
            // Subscribe to query updates to trigger refresh on job changes
            const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
                if (event.type === 'updated' && 
                    Array.isArray(event.query.queryKey) && 
                    (event.query.queryKey[0] === 'jobs' || event.query.queryKey[0] === 'jobUpdates')) {
                    checkItems();
                }
            });
            return () => {
                if (intervalRef.current) {
                    clearInterval(intervalRef.current);
                }
                unsubscribe();
            };
        }
    }, [isWatching, startTime, hasConfigsWithIds, checkItems, queryClient]);

    return {
        isWatching,
        results,
        lastCheckTime,
        startWatching,
        stopWatching,
        resetWatcher
    };
}
