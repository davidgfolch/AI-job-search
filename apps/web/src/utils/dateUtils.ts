
/**
 * Calculates the lapsed time from a given date string to now.
 * Returns a human-readable string like "today", "yesterday", "X days", "X week(s)", or "X month(s)".
 * @param dateString ISO date string
 */

interface LapsedTime {
    short: string;
    long: string;
}

const getLapsedTime = (diffDays: number): LapsedTime => {
    if (diffDays === 0) {
        return { short: 'today', long: 'today' };
    } else if (diffDays === 1) {
        return { short: '1d ago', long: '1 day ago' }; // Explicitly handle 1 day case for singular "day" 
        // Wait, the user requirement for short was "Yesterday" removed? The user diff removed "Yesterday". 
        // User diff:
        // -    } else if (diffDays === 1) {
        // -        return 'yesterday';
        //      } else if (diffDays < 7) {
        //          return `${diffDays}d ago`;
        
        // So for diffDays=1, it hits <7 and returns "1d ago".
        // And for long, it should probably be "1 day ago".
    }
    
    if (diffDays < 7) {
        const dayStr = diffDays === 1 ? 'day' : 'days';
        return { 
            short: `${diffDays}d ago`, 
            long: `${diffDays} ${dayStr} ago` 
        };
    } else if (diffDays < 30) {
        const weeks = Math.floor(diffDays / 7);
        const weekStr = weeks === 1 ? 'week' : 'weeks';
        return { 
            short: `${weeks}w ago`, 
            long: `${weeks} ${weekStr} ago` 
        };
    } else {
        const months = Math.floor(diffDays / 30);
        const monthStr = months === 1 ? 'month' : 'months';
        return { 
            short: `${months}m ago`, 
            long: `${months} ${monthStr} ago` 
        };
    }
};

export const calculateLapsedTime = (dateString: string | null | undefined): string => {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';

    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        const hours = date.getHours().toString(); // No padding needed for hours based on user request example "9:10"
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }
    
    return getLapsedTime(diffDays).short;
};

export const calculateLapsedTimeDetail = (dateString: string | null | undefined): string => {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';

    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    return getLapsedTime(diffDays).long;
};
