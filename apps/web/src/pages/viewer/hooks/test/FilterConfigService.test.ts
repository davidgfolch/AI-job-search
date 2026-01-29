import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FilterConfigService } from '../FilterConfigService';
import { persistenceApi } from '../../../common/api/CommonPersistenceApi';
import type { FilterConfig } from '../../components/configurations/hooks/useFilterConfigurations';

vi.mock('../../../common/api/CommonPersistenceApi', () => ({
  persistenceApi: {
    getValue: vi.fn(),
    setValue: vi.fn(),
  },
}));

describe('FilterConfigService', () => {
  let service: FilterConfigService;
  const mockDefaults: FilterConfig[] = [
    { name: 'Default 1', filters: {} },
    { name: 'Default 2', filters: {} },
  ];

  beforeEach(() => {
    service = new FilterConfigService();
    vi.clearAllMocks();
  });

  describe('load', () => {
    it('returns stored configs when available', async () => {
      const stored: FilterConfig[] = [{ name: 'Stored', filters: {} }];
      vi.mocked(persistenceApi.getValue).mockResolvedValue(stored);
      const result = await service.load(mockDefaults);
      expect(result).toEqual(stored);
    });

    it('returns defaults when no stored configs', async () => {
      vi.mocked(persistenceApi.getValue).mockResolvedValue([]);
      const result = await service.load(mockDefaults);
      expect(result).toEqual(mockDefaults);
    });

    it('returns defaults when stored value is not an array', async () => {
      vi.mocked(persistenceApi.getValue).mockResolvedValue(null);
      const result = await service.load(mockDefaults);
      expect(result).toEqual(mockDefaults);
    });
  });

  describe('save', () => {
    it('saves configs to persistence', async () => {
      const configs: FilterConfig[] = [{ name: 'Config 1', filters: {} }];
      await service.save(configs);
      expect(persistenceApi.setValue).toHaveBeenCalledWith('filter_configurations', configs);
    });

    it('limits configs to maximum of 30', async () => {
      const manyConfigs: FilterConfig[] = Array.from({ length: 40 }, (_, i) => ({
        name: `Config ${i}`,
        filters: {},
      }));
      await service.save(manyConfigs);
      expect(persistenceApi.setValue).toHaveBeenCalledWith(
        'filter_configurations',
        manyConfigs.slice(0, 30)
      );
    });
  });

  describe('export', () => {
    it('returns stored configs', async () => {
      const stored: FilterConfig[] = [{ name: 'Export', filters: {} }];
      vi.mocked(persistenceApi.getValue).mockResolvedValue(stored);
      const result = await service.export();
      expect(result).toEqual(stored);
    });

    it('returns empty array when no stored configs', async () => {
      vi.mocked(persistenceApi.getValue).mockResolvedValue(null);
      const result = await service.export();
      expect(result).toEqual([]);
    });
  });
});
