import { useCallback } from 'react';
import type { FilterConfig } from './useFilterConfigurations';
import type { FilterConfigService } from '../../../hooks/FilterConfigService';

interface UseConfigTogglesProps {
    savedConfigs: FilterConfig[];
    setSavedConfigs: (configs: FilterConfig[]) => void;
    service: FilterConfigService;
    notify: (msg: string, type: 'success' | 'error') => void;
}

export function useConfigToggles({ savedConfigs, setSavedConfigs, service, notify }: UseConfigTogglesProps) {
    
    const toggleProperty = useCallback(async (
        name: string, 
        property: keyof FilterConfig, 
        serviceMethod: (id: number, value: boolean) => Promise<void> | Promise<void>,
        errorMsg: string
    ) => {
        const configIndex = savedConfigs.findIndex(c => c.name === name);
        if (configIndex === -1) return;

        const config = savedConfigs[configIndex];
        // Ensure boolean toggling, default to false if undefined
        const newValue = !(config[property] as boolean);

        const updatedConfigs = [...savedConfigs];
        updatedConfigs[configIndex] = {
            ...config,
            [property]: newValue
        };

        // Optimistic update
        setSavedConfigs(updatedConfigs);

        try {
            if (config.id !== undefined) {
                await serviceMethod(config.id, newValue);
            } else {
                // Fallback for configs without ID
                await service.save(updatedConfigs);
            }
        } catch (e) {
            console.error('Failed to save configuration', e);
            notify(errorMsg, 'error');
            // Revert on failure
            updatedConfigs[configIndex] = config;
            setSavedConfigs([...updatedConfigs]);
        }
    }, [savedConfigs, setSavedConfigs, service, notify]);

    const toggleNotification = useCallback((name: string) => {
        // Special case for notification: it persists via service.save for generic update
        // But the original code persisted via service.save specifically.
        // Let's adapt to maintain exact behavior:
        // Original behavior: update config object, call service.save(allConfigs)
        // Actually original updated specific config and called service.save(allConfigs)
        // Which is slightly different from updateStatistics/updatePinned which have specific methods.
        
        // Wait, looking at original code:
        // toggleNotification calls service.save(updatedConfigs) 
        // toggleStatistics calls service.updateStatistics(id, value) OR service.save(updatedConfigs)
        // togglePin calls service.updatePinned(id, value) OR service.save(updatedConfigs)
        
        // So toggleNotification is the only one NOT using a specific update method? 
        // Let's check FilterConfigService.ts...
        // It has updateStatistics and updatePinned. It does NOT have updateNotification.
        // So validation of my assumption is correct.
        
        const configIndex = savedConfigs.findIndex(c => c.name === name);
        if (configIndex === -1) return;

        const updatedConfigs = [...savedConfigs];
        updatedConfigs[configIndex] = {
            ...updatedConfigs[configIndex],
            notify: !updatedConfigs[configIndex].notify
        };

        const executeSave = async () => {
             try {
                await service.save(updatedConfigs);
                setSavedConfigs(updatedConfigs);
            } catch (e) {
                console.error('Failed to save configuration', e);
                notify('Failed to update notification setting', 'error');
            }
        };
        executeSave();
    }, [savedConfigs, setSavedConfigs, service, notify]);


    const toggleStatistics = useCallback((name: string) => 
        toggleProperty(
            name, 
            'statistics', 
            (id, val) => service.updateStatistics(id, val),
            'Failed to update statistics setting'
        ), 
    [toggleProperty, service]);

    const togglePin = useCallback((name: string) => 
        toggleProperty(
            name, 
            'pinned', 
            (id, val) => service.updatePinned(id, val),
            'Failed to update pin setting'
        ), 
    [toggleProperty, service]);

    return {
        toggleNotification,
        toggleStatistics,
        togglePin
    };
}
