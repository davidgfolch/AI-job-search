import { useState, useEffect, useRef } from 'react';

interface UseFilterExpandedProps {
    configCount?: number;
}

export function useFilterExpanded({ configCount }: UseFilterExpandedProps = {}) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [isInitialized, setIsInitialized] = useState(true);
    const isMounted = useRef(true);

    useEffect(() => {
        isMounted.current = true;
        
        if (configCount !== undefined) {
            setIsExpanded(configCount === 0);
            setIsInitialized(true);
        }
        
        return () => { isMounted.current = false; };
    }, [configCount]);
    
    return { isExpanded: isInitialized && isExpanded, setIsExpanded, isInitialized };
}
