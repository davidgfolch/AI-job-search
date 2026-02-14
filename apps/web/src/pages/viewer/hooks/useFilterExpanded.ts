import { useState, useEffect, useRef } from 'react';

interface UseFilterExpandedProps {
    configCount?: number;
}

export function useFilterExpanded({ configCount }: UseFilterExpandedProps = {}) {
    const [isExpanded, setIsExpanded] = useState(true);
    const [isInitialized, setIsInitialized] = useState(false);
    const isMounted = useRef(true);
    
    useEffect(() => {
        isMounted.current = true;
        
        if (configCount !== undefined) {
            setIsExpanded(configCount === 0);
            setIsInitialized(true);
            return () => { isMounted.current = false; };
        }
        
        // Fallback: if no configCount provided, assume expanded (backwards compatibility)
        setIsExpanded(true);
        setIsInitialized(true);
        return () => { isMounted.current = false; };
    }, [configCount]);
    
    return { isExpanded, setIsExpanded, isInitialized };
}
