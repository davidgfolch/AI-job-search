import { useState, useEffect } from 'react';
import { filterConfigsApi } from '../api/FilterConfigurationsApi';
export function useFilterExpanded() {
    const [isExpanded, setIsExpanded] = useState(true);
    const [isInitialized, setIsInitialized] = useState(false);
    useEffect(() => {
        const checkConfigurations = async () => {
            try {
                const configs = await filterConfigsApi.getAll();
                setIsExpanded(configs.length === 0);
            } catch (error) {
                console.error('Failed to check filter configurations:', error);
                setIsExpanded(true);
            } finally {
                setIsInitialized(true);
            }
        };
        checkConfigurations();
    }, []);
    return { isExpanded, setIsExpanded, isInitialized };
}
