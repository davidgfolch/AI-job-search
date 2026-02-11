import { useState, useEffect, useRef, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { FilterConfig } from './useFilterConfigurations';
import { jobsApi } from '../../../api/ViewerApi';
import { notificationService } from '../../../../../common/services/NotificationService';
import type { WatcherResult, UseFilterWatcherProps } from './useFilterWatcher.types';
import { POLLING_INTERVAL } from './useFilterWatcher.types';
import { getCutoffMap, processNotifications } from './useFilterWatcher.utils';
import { persistenceApi } from '../../../../../pages/common/api/CommonPersistenceApi';

export const LAST_WATCHER_CHECK_TIME_KEY = 'last_watcher_check_time';

export { POLLING_INTERVAL };
export type { WatcherResult };

export function useFilterWatcher({ savedConfigs }: UseFilterWatcherProps) {
    const [isWatching, setIsWatching] = useState(true);
    const [results, setResults] = useState<Record<string, WatcherResult>>({});
    const [lastCheckTime, setLastCheckTime] = useState<Date | null>(new Date());
    const [startTime, setStartTime] = useState<Date | null>(new Date());
    const [serverOffset, setServerOffset] = useState<number | null>(null);
    const configStartTimes = useRef<Record<string, Date>>({});
    const notifiedCountsRef = useRef<Record<string, number>>({});
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const savedConfigsRef = useRef(savedConfigs as FilterConfig[]);
    const isMounted = useRef(true);
    const lastRequestIdRef = useRef(0);
    const checkTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const justResetRef = useRef<Set<string>>(new Set(savedConfigs.map(c => c.name)));
    const queryClient = useQueryClient();

    useEffect(() => {
        if (isWatching) notificationService.requestPermission();
        jobsApi.getSystemTimezone().then(data => setServerOffset(data.offset_minutes))
            .catch(() => setServerOffset(-new Date().getTimezoneOffset()));
        const loadPersistedTime = async () => {
            const storedTime = await persistenceApi.getValue<string>(LAST_WATCHER_CHECK_TIME_KEY);
            if (storedTime) {
                const date = new Date(storedTime);
                if (!isNaN(date.getTime())) {
                    setStartTime(date);
                    setLastCheckTime(date);
                }
            }
        };
        loadPersistedTime();
        isMounted.current = true;
        return () => { isMounted.current = false; };
    }, []);

    useEffect(() => { savedConfigsRef.current = savedConfigs as FilterConfig[]; }, [savedConfigs]);

    const checkItems = useCallback(async () => {
        if (!startTime) return;
        const requestId = ++lastRequestIdRef.current;
        const configIdsWithNames = savedConfigsRef.current
            .filter(c => c.id && c.watched !== false)
            .map(c => ({ id: c.id!, name: c.name }));
        if (configIdsWithNames.length === 0) return;
        const justReset = new Set(justResetRef.current);
        try {
            const cutoffMap = getCutoffMap(configIdsWithNames, startTime, configStartTimes.current, serverOffset);
            const statsMap = await jobsApi.getWatcherStats(cutoffMap);
            if (isMounted.current && requestId === lastRequestIdRef.current) {
                const newResults: Record<string, WatcherResult> = {};
                configIdsWithNames.forEach(({ id, name }) => {
                    const stats = statsMap[id];
                    if (stats) {
                        const isReset = justReset.has(name);
                        newResults[name] = { total: stats.total, newItems: isReset ? 0 : stats.new_items };
                        if (isReset && stats.new_items === 0) justResetRef.current.delete(name);
                    }
                });
                setResults(newResults);
                const now = new Date();
                setLastCheckTime(now);
                persistenceApi.setValue(LAST_WATCHER_CHECK_TIME_KEY, now.toISOString());
                processNotifications(newResults, savedConfigsRef.current, notifiedCountsRef.current);
            }
        } catch (error) { console.error('Error checking watcher stats:', error); }
    }, [startTime, serverOffset]);

    const startWatching = () => {
        notificationService.requestPermission();
        setIsWatching(true);
        const now = new Date();
        setStartTime(now);
        setLastCheckTime(now);
        setResults({});
        justResetRef.current = new Set(savedConfigsRef.current.map(c => c.name));
        configStartTimes.current = {};
        notifiedCountsRef.current = {};
    };

    const stopWatching = () => {
        setIsWatching(false);
        setStartTime(null);
        setLastCheckTime(null);
        setResults({});
        configStartTimes.current = {};
        notifiedCountsRef.current = {};
        if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; }
    };

    const resetWatcher = (configName: string) => {
        configStartTimes.current[configName] = new Date(Date.now() + 5000);
        notifiedCountsRef.current[configName] = 0;
        justResetRef.current.add(configName);
        lastRequestIdRef.current++;
        setResults(prev => ({
            ...prev,
            [configName]: { total: prev[configName]?.total ?? 0, newItems: 0 }
        }));
    };

    useEffect(() => {
        const hasConfigsWithIds = savedConfigsRef.current.some(c => c.id);
        if (isWatching && startTime && hasConfigsWithIds) {
            const debouncedCheck = () => {
                if (checkTimeoutRef.current) clearTimeout(checkTimeoutRef.current);
                checkTimeoutRef.current = setTimeout(checkItems, 200);
            };
            debouncedCheck();
            intervalRef.current = setInterval(checkItems, POLLING_INTERVAL);
            const unsubscribe = queryClient.getQueryCache().subscribe((event) => {
                if (event.type === 'updated' && Array.isArray(event.query.queryKey) && 
                    (event.query.queryKey[0] === 'jobs' || event.query.queryKey[0] === 'jobUpdates')) {
                    debouncedCheck();
                }
            });
            return () => {
                if (intervalRef.current) clearInterval(intervalRef.current);
                if (checkTimeoutRef.current) clearTimeout(checkTimeoutRef.current);
                unsubscribe();
            };
        }
    }, [isWatching, startTime, checkItems, queryClient, savedConfigs]);
    return { isWatching, results, lastCheckTime, startWatching, stopWatching, resetWatcher };
}
