import { useState } from 'react';

interface UseFilterExpandedProps {
    configCount?: number;
}

export function useFilterExpanded({ configCount }: UseFilterExpandedProps = {}) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isInitialized, setIsInitialized] = useState(true);
    const [lastConfigCount, setLastConfigCount] = useState<number | undefined>(undefined);

    if (configCount !== undefined && lastConfigCount !== configCount) {
        setLastConfigCount(configCount);
        setIsExpanded(configCount === 0);
        setIsInitialized(true);
    }

    return { isExpanded: isInitialized && isExpanded, setIsExpanded, isInitialized };
}
