import { notificationService } from '../../../../../common/services/NotificationService';
import type { WatcherResult } from './useFilterWatcher.types';
import type { FilterConfig } from './useFilterConfigurations';

export function getCutoffMap(
    configIdsWithNames: Array<{ id: number; name: string }>,
    startTime: Date,
    configStartTimes: Record<string, Date>,
    serverOffset: number | null
): Record<number, string> {
    const cutoffMap: Record<number, string> = {};
    configIdsWithNames.forEach(c => {
        const configStartTime = configStartTimes[c.name] || startTime;
        if (configStartTime) {
            const effectiveOffsetMinutes = serverOffset !== null ? serverOffset : -configStartTime.getTimezoneOffset();
            const tzOffsetMs = effectiveOffsetMinutes * 60000;
            const localISOTime = new Date(configStartTime.getTime() + tzOffsetMs).toISOString().slice(0, -1);
            cutoffMap[c.id] = localISOTime;
        }
    });
    return cutoffMap;
}

export function processNotifications(
    newResults: Record<string, WatcherResult>,
    configsToCheck: FilterConfig[],
    notifiedCounts: Record<string, number>
) {
    const notificationAggregator: string[] = [];
    Object.entries(newResults).forEach(([name, result]) => {
        const prevCount = notifiedCounts[name] || 0;
        if (result.newItems > prevCount) {
            notifiedCounts[name] = result.newItems;
            const config = configsToCheck.find(c => c.name === name);
            if (config && config.watched) {
                notificationAggregator.push(`${name} (${result.newItems})`);
            }
        }
    });
    if (notificationAggregator.length > 0) {
        notificationService.notify(`New jobs found`, {
            body: notificationAggregator.join(', '),
        });
    }
}
