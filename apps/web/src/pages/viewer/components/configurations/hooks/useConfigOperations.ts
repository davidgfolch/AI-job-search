import { useCallback } from 'react';
import type { JobListParams } from '../../../api/ViewerApi';
import type { FilterConfig } from './useFilterConfigurations';
import type { FilterConfigService } from '../../../hooks/FilterConfigService';
import { normalizeFilters } from '../utils/filterNormalization';
import type { ConfirmationModal } from './useConfirmationModal';

interface UseConfigOperationsProps {
  service: FilterConfigService;
  savedConfigs: FilterConfig[];
  setSavedConfigs: (configs: FilterConfig[]) => void;
  currentFilters: JobListParams;
  configName: string;
  setConfigName: (name: string) => void;
  setIsOpen: (isOpen: boolean) => void;
  setSavedConfigName: (name: string) => void;
  onLoadConfig: (filters: JobListParams, name: string) => void;
  notify: (message: string, type: 'success' | 'error') => void;
  confirmModal: ConfirmationModal;
}

export const useConfigOperations = ({
  service,
  savedConfigs,
  setSavedConfigs,
  currentFilters,
  configName,
  setConfigName,
  setIsOpen,
  setSavedConfigName,
  onLoadConfig,
  notify,
  confirmModal,
}: UseConfigOperationsProps) => {
  const saveConfiguration = useCallback(async () => {
    if (!configName.trim()) {
      notify('Please enter a name for the configuration', 'error');
      return;
    }
    const newConfig: FilterConfig = {
      name: configName.trim(),
      filters: currentFilters,
    };
    const filtered = savedConfigs.filter(c => c.name !== newConfig.name);
    const updated = [newConfig, ...filtered];
    try {
      await service.save(updated);
      setSavedConfigs(updated);
      setConfigName('');
      setIsOpen(false);
      notify(`Configuration "${newConfig.name}" saved!`, 'success');
    } catch (e) {
      console.error('Failed to save configuration', e);
      notify('Failed to save configuration', 'error');
    }
  }, [
    configName,
    currentFilters,
    savedConfigs,
    service,
    setSavedConfigs,
    setConfigName,
    setIsOpen,
    notify,
  ]);

  const loadConfiguration = useCallback((config: FilterConfig) => {
    const filtersToLoad = normalizeFilters(config.filters);
    onLoadConfig(filtersToLoad, config.name);
    setConfigName(config.name);
    setSavedConfigName(config.name);
    setIsOpen(false);
  }, [onLoadConfig, setConfigName, setSavedConfigName, setIsOpen]);

  const deleteConfiguration = useCallback(async (name: string, event: React.MouseEvent) => {
    event.stopPropagation();
    confirmModal.confirm(`Delete configuration "${name}"?`, async () => {
      const updated = savedConfigs.filter(c => c.name !== name);
      try {
        await service.save(updated);
        setSavedConfigs(updated);
        if (configName === name) {
          setConfigName('');
          setSavedConfigName('');
        }
      } catch (e) {
        console.error('Failed to delete configuration', e);
        notify('Failed to delete configuration', 'error');
      }
    });
  }, [confirmModal, savedConfigs, service, setSavedConfigs, notify, configName, setConfigName, setSavedConfigName]);

  const exportToDefaults = useCallback(async () => {
    try {
      const stored = await service.export();
      if (!stored || stored.length === 0) {
        notify('No configurations to export.', 'error');
        return;
      }
      const jsonString = JSON.stringify(stored, null, 4);
      const blob = new Blob([jsonString], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'defaultFilterConfigurations.json';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      notify('Configuration downloaded!', 'success');
    } catch (err) {
      console.error('Failed to copy', err);
      notify('Failed to copy to clipboard. Check console.', 'error');
    }
  }, [service, notify]);

  const reorderConfigurations = useCallback(async (newConfigs: FilterConfig[]) => {
    try {
      const configsWithOrdering = newConfigs.map((config, index) => ({
        ...config,
        ordering: index
      }));
      setSavedConfigs(configsWithOrdering);
      await service.save(configsWithOrdering);
    } catch (e) {
      console.error('Failed to reorder configurations', e);
      notify('Failed to save new order', 'error');

    }
  }, [service, setSavedConfigs, notify]);

  return {
    saveConfiguration,
    loadConfiguration,
    deleteConfiguration,
    exportToDefaults,
    reorderConfigurations,
  };
};
