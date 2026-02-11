/**
 * Calculates the lapsed time from a given date string to now.
 * Returns a human-readable string like "today", "yesterday", "X days", "X week(s)", or "X month(s)".
 * @param dateString ISO date string
 */

interface LapsedTime {
    short: string;
    long: string;
}

function getDayDiff(date: Date, now: Date): number {
    const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffTime = nowOnly.getTime() - dateOnly.getTime();
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}

function getLapsedTime(diffDays: number): LapsedTime {
    if (diffDays === 0) {
        return { short: 'today', long: 'today' };
    } else if (diffDays === 1) {
        return { short: '1d', long: 'yesterday' };
    }
    if (diffDays < 7) {
        const dayStr = diffDays === 1 ? 'day' : 'days';
        return {
            short: `${diffDays}d`,
            long: `${diffDays} ${dayStr} ago`
        };
    } else if (diffDays < 30) {
        const weeks = Math.floor(diffDays / 7);
        const weekStr = weeks === 1 ? 'week' : 'weeks';
        return {
            short: `${weeks}w`,
            long: `${weeks} ${weekStr} ago`
        };
    }
    const months = Math.floor(diffDays / 30);
    const monthStr = months === 1 ? 'month' : 'months';
    return {
        short: `${months}m`,
        long: `${months} ${monthStr} ago`
    };
}

function getLapsed(dateString: string | null | undefined): { diffDays: number, date: Date, now: Date } | null {
    if (!dateString) return null;
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return null;
    const now = new Date();
    const diffDays = getDayDiff(date, now);
    return { diffDays, date, now };
}
const getLapsedParts = (dateString: string | null | undefined): { diffDays: number, hours: string, minutes: string } | null => {
    const lapsed = getLapsed(dateString);
    if (!lapsed) return null;
    const { diffDays, date } = lapsed;
    const hours = date.getHours().toString();
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return { diffDays, hours, minutes }
}

export const calculateLapsedTime = (dateString: string | null | undefined): string => {
    const { diffDays, hours, minutes } = getLapsedParts(dateString) || {}
    if (diffDays === undefined) return '-';
    if (diffDays === 0) {
        return `${hours}:${minutes}`;
    }
    return getLapsedTime(diffDays).short + (diffDays <2? ` ${hours}:${minutes}`:'');
};

export const calculateLapsedTimeDetail = (dateString: string | null | undefined): string => {
    const { diffDays, hours, minutes } = getLapsedParts(dateString) || {}
    if (diffDays === undefined) return '-';
    return getLapsedTime(diffDays).long + ` ${hours}:${minutes}`;
};
