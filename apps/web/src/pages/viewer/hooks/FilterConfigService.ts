import { filterConfigsApi, type FilterConfiguration as BackendFilterConfiguration } from '../api/FilterConfigurationsApi';
import { persistenceApi } from "../../common/api/CommonPersistenceApi";
import type { FilterConfig } from '../components/configurations/hooks/useFilterConfigurations';

export class FilterConfigService {
  private readonly localStorageKey = 'filter_configurations';
  private readonly migrationKey = 'filter_configurations_migrated_to_backend';
  private readonly maxConfigs = 30;

  async load(defaults: FilterConfig[]): Promise<FilterConfig[]> {
    try {
      const backendConfigs = await filterConfigsApi.getAll();
      await this.migrateFromLocalStorageIfNeeded(backendConfigs);
      const configs = backendConfigs.map(bc => ({
        id: bc.id,
        name: bc.name,
        filters: bc.filters,
        notify: bc.notify,
        statistics: bc.statistics,
        pinned: bc.pinned,
        ordering: bc.ordering
      }));
      return this.mergeDefaults(configs, defaults);
    } catch (error) {
      console.error('Failed to load filter configurations from backend:', error);
      const stored = await persistenceApi.getValue<FilterConfig[]>(this.localStorageKey);
      const configs = stored && Array.isArray(stored) ? stored : [];
      return this.mergeDefaults(configs, defaults);
    }
  }

  async updateStatistics(id: number, statistics: boolean): Promise<void> {
    await filterConfigsApi.update(id, { statistics });
  }

  async updatePinned(id: number, pinned: boolean): Promise<void> {
    await filterConfigsApi.update(id, { pinned });
  }

  async save(configs: FilterConfig[]): Promise<void> {
    try {
      const limited = configs.slice(0, this.maxConfigs);
      // Get existing backend configs
      const backendConfigs = await filterConfigsApi.getAll();
      const backendMap = new Map(backendConfigs.map(bc => [bc.name, bc]));
      // Update or create each config
      for (const [index, config] of limited.entries()) {
        const existing = backendMap.get(config.name);
        if (existing) {
          // Update if changed
          await filterConfigsApi.update(existing.id, {
            filters: config.filters,
            notify: config.notify,
            statistics: config.statistics,
            pinned: config.pinned,
            ordering: index
          });
        } else {
          // Create new
          await filterConfigsApi.create({
            name: config.name,
            filters: config.filters,
            notify: config.notify,
            statistics: config.statistics,
            pinned: config.pinned,
            ordering: index
          });
        }
      }
      
      // Delete configs that are no longer in the list
      const currentNames = new Set(limited.map(c => c.name));
      for (const backendConfig of backendConfigs) {
        if (!currentNames.has(backendConfig.name)) {
          await filterConfigsApi.delete(backendConfig.id);
        }
      }
    } catch (error) {
      console.error('Failed to save filter configurations to backend:', error);
      // Fallback to localStorage if backend fails
      const limited = configs.slice(0, this.maxConfigs);
      await persistenceApi.setValue(this.localStorageKey, limited);
    }
  }

  async export(): Promise<FilterConfig[]> {
    try {
      const backendConfigs = await filterConfigsApi.getAll();
      return backendConfigs.map(bc => ({
        name: bc.name,
        filters: bc.filters,
        notify: bc.notify,
        statistics: bc.statistics,
        pinned: bc.pinned
      }));
    } catch (error) {
      console.error('Failed to export filter configurations:', error);
      const stored = await persistenceApi.getValue<FilterConfig[]>(this.localStorageKey);
      return stored && Array.isArray(stored) ? stored : [];
    }
  }

  private async migrateFromLocalStorageIfNeeded(backendConfigs: BackendFilterConfiguration[]): Promise<void> {
    const migrated = localStorage.getItem(this.migrationKey);
    if (migrated === 'true') {
      return; // Already migrated
    }

    try {
      const localStorageConfigs = await persistenceApi.getValue<FilterConfig[]>(this.localStorageKey);
      if (!localStorageConfigs || localStorageConfigs.length === 0) {
        localStorage.setItem(this.migrationKey, 'true');
        return;
      }

      // const backendConfigs = await filterConfigsApi.getAll(); // Removed duplicate call
      const backendNames = new Set(backendConfigs.map(bc => bc.name));

      // Migrate user-created configs (skip defaults that are already seeded)
      for (const config of localStorageConfigs) {
        if (!backendNames.has(config.name)) {
          await filterConfigsApi.create({
            name: config.name,
            filters: config.filters,
            notify: config.notify || false,
            statistics: config.statistics || true,
            pinned: config.pinned || false,
            ordering: 0 // Default ordering for migrated configs
          });
        }
      }

      localStorage.setItem(this.migrationKey, 'true');
    } catch (error) {
      console.error('Failed to migrate filter configurations:', error);
      // Don't set migration flag on failure so we can retry
    }
  }

  private mergeDefaults(stored: FilterConfig[], defaults: FilterConfig[]): FilterConfig[] {
    // If we have stored configs, just return them (don't merge defaults)
    // The backend already handles seeding defaults
    if (stored.length > 0) return stored;
    
    // Only use defaults if no stored configs at all
    return defaults;
  }
}
