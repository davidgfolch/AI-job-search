import { useCallback } from 'react';
import type { JobListParams } from '../../../api/jobs';
import type { FilterConfig } from './useFilterConfigurations';
import type { FilterConfigService } from '../../../services/FilterConfigService';
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
      } catch (e) {
        console.error('Failed to delete configuration', e);
        notify('Failed to delete configuration', 'error');
      }
    });
  }, [confirmModal, savedConfigs, service, setSavedConfigs, notify]);

  const exportToDefaults = useCallback(async () => {
    try {
      const stored = await service.export();
      if (!stored || stored.length === 0) {
        notify('No configurations to export.', 'error');
        return;
      }
      const exportString = `// Paste this into apps/web/src/data/defaults.ts\nexport const defaultFilterConfigurations = ${JSON.stringify(stored, null, 4)};`;
      await navigator.clipboard.writeText(exportString);
      notify('Configuration copied to clipboard! Paste into defaults.ts', 'success');
    } catch (err) {
      console.error('Failed to copy', err);
      notify('Failed to copy to clipboard. Check console.', 'error');
    }
  }, [service, notify]);

  return {
    saveConfiguration,
    loadConfiguration,
    deleteConfiguration,
    exportToDefaults,
  };
};
