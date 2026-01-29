import { persistenceApi } from '../api/persistence';
import type { FilterConfig } from '../components/configurations/hooks/useFilterConfigurations';

export class FilterConfigService {
  private readonly storageKey = 'filter_configurations';
  private readonly maxConfigs = 30;

  async load(defaults: FilterConfig[]): Promise<FilterConfig[]> {
    const stored = await persistenceApi.getValue<FilterConfig[]>(this.storageKey);
    const configs = stored && Array.isArray(stored) ? stored : [];
    return this.mergeDefaults(configs, defaults);
  }

  async save(configs: FilterConfig[]): Promise<void> {
    const limited = configs.slice(0, this.maxConfigs);
    await persistenceApi.setValue(this.storageKey, limited);
  }

  async export(): Promise<FilterConfig[]> {
    const stored = await persistenceApi.getValue<FilterConfig[]>(this.storageKey);
    return stored && Array.isArray(stored) ? stored : [];
  }

  private mergeDefaults(stored: FilterConfig[], defaults: FilterConfig[]): FilterConfig[] {
    if (stored.length === 0) return defaults;
    return stored;
  }
}
