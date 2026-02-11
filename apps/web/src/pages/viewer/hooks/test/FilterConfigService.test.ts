import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FilterConfigService } from '../FilterConfigService';
import { filterConfigsApi } from '../../api/FilterConfigurationsApi';
import { persistenceApi } from '../../../common/api/CommonPersistenceApi';
import type { FilterConfig } from '../../components/configurations/hooks/useFilterConfigurations';

vi.mock('../../api/FilterConfigurationsApi');
vi.mock('../../../common/api/CommonPersistenceApi');

describe('FilterConfigService', () => {
  let service: FilterConfigService;
  const mockDefaults: FilterConfig[] = [
    { name: 'Default 1', filters: { page: 1 }, watched: false },
    { name: 'Default 2', filters: { page: 2 }, watched: false }
  ];

  beforeEach(() => {
    service = new FilterConfigService();
    vi.clearAllMocks();
    localStorage.clear();
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  describe('load', () => {
    it('should load configurations from backend API', async () => {
      const mockBackendConfigs = [
        { id: 1, name: 'Config 1', filters: { page: 1 }, watched: false, statistics: true, pinned: false, created: '2024-01-01', modified: null },
        { id: 2, name: 'Config 2', filters: { page: 2 }, watched: true, statistics: true, pinned: false, created: '2024-01-02', modified: null }
      ];
      vi.mocked(filterConfigsApi.getAll).mockResolvedValue(mockBackendConfigs);
      vi.mocked(persistenceApi.getValue).mockResolvedValue(null);

      const result = await service.load(mockDefaults);

      expect(filterConfigsApi.getAll).toHaveBeenCalledOnce();
      expect(result).toHaveLength(2);
      expect(result[0].name).toBe('Config 1');
      expect(result[1].watched).toBe(true);
    });

    it('should return runtime defaults if backend returns empty', async () => {
      vi.mocked(filterConfigsApi.getAll).mockResolvedValue([]);
      vi.mocked(persistenceApi.getValue).mockResolvedValue(null);

      const result = await service.load(mockDefaults);

      expect(result).toEqual(mockDefaults);
    });

    it('should fallback to localStorage if backend fails', async () => {
      const localStorageConfigs = [
        { name: 'Local Config', filters: { page: 1 }, watched: false }
      ];
      vi.mocked(filterConfigsApi.getAll).mockRejectedValue(new Error('Network error'));
      vi.mocked(persistenceApi.getValue).mockResolvedValue(localStorageConfigs);

      const result = await service.load(mockDefaults);

      // Should just return localStorage configs (no merge since we have data)
      expect(result).toEqual(localStorageConfigs);
    });

    it('should migrate localStorage configs on first load', async () => {
      const backendConfigs = [
        { id: 1, name: 'Backend Config', filters: { page: 1 }, watched: false, statistics: true, pinned: false, created: '2024-01-01', modified: null }
      ];
      const localStorageConfigs = [
        { name: 'Local Config', filters: { page: 2 }, watched: false }
      ];
      
      vi.mocked(filterConfigsApi.getAll).mockResolvedValue(backendConfigs);
      vi.mocked(persistenceApi.getValue).mockResolvedValue(localStorageConfigs);
      vi.mocked(filterConfigsApi.create).mockResolvedValue({
        id: 2, name: 'Local Config', filters: { page: 2 }, watched: false, statistics: true, pinned: false, created: '2024-01-01', modified: null
      });

      await service.load(mockDefaults);

      // Migration should create the local config in backend
      expect(filterConfigsApi.create).toHaveBeenCalledWith({
        name: 'Local Config',
        filters: { page: 2 },
        watched: false,
        statistics: true,
        pinned: false,
        ordering: 0
      });
    });
  });

  describe('save', () => {
    it('should save configurations to backend API', async () => {
      const configs: FilterConfig[] = [
        { name: 'Config 1', filters: { page: 1 }, watched: false }
      ];
      const backendConfigs = [
        { id: 1, name: 'Config 1', filters: { page: 1 }, watched: false, statistics: true, pinned: false, created: '2024-01-01', modified: null }
      ];

      vi.mocked(filterConfigsApi.getAll).mockResolvedValue(backendConfigs);
      vi.mocked(filterConfigsApi.update).mockResolvedValue(backendConfigs[0]);

      await service.save(configs);

      expect(filterConfigsApi.update).toHaveBeenCalledWith(1, {
        filters: { page: 1 },
        watched: false,
        ordering: 0,
        pinned: undefined,
        statistics: undefined
      });
    });

    it('should create new configs if they do not exist in backend', async () => {
      const configs: FilterConfig[] = [
        { name: 'New Config', filters: { page: 3 }, watched: true, statistics: true }
      ];

      vi.mocked(filterConfigsApi.getAll).mockResolvedValue([]);
      vi.mocked(filterConfigsApi.create).mockResolvedValue({
        id: 1, name: 'New Config', filters: { page: 3 }, watched: true, statistics: true, pinned: false, created: '2024-01-01', modified: null
      });

      await service.save(configs);

      expect(filterConfigsApi.create).toHaveBeenCalledWith({
        name: 'New Config',
        filters: { page: 3 },
        watched: true,
        statistics: true,
        ordering: 0,
        pinned: undefined
      });
    });

    it('should delete configs that are no longer in the list', async () => {
      const configs: FilterConfig[] = [];
      const backendConfigs = [
        { id: 1, name: 'Old Config', filters: { page: 1 }, watched: false, statistics: true, pinned: false, created: '2024-01-01', modified: null }
      ];

      vi.mocked(filterConfigsApi.getAll).mockResolvedValue(backendConfigs);
      vi.mocked(filterConfigsApi.delete).mockResolvedValue();

      await service.save(configs);

      expect(filterConfigsApi.delete).toHaveBeenCalledWith(1);
    });

    it('should fallback to localStorage if backend save fails', async () => {
      const configs: FilterConfig[] = [
        { name: 'Config', filters: { page: 1 }, watched: false }
      ];

      vi.mocked(filterConfigsApi.getAll).mockRejectedValue(new Error('Network error'));
      vi.mocked(persistenceApi.setValue).mockResolvedValue();

      await service.save(configs);

      expect(persistenceApi.setValue).toHaveBeenCalledWith('filter_configurations', configs);
    });
  });

  describe('export', () => {
    it('should export configurations from backend API', async () => {
      const mockBackendConfigs = [
        { id: 1, name: 'Config 1', filters: { page: 1 }, watched: false, statistics: true, pinned: false, created: '2024-01-01', modified: null }
      ];
      vi.mocked(filterConfigsApi.getAll).mockResolvedValue(mockBackendConfigs);

      const result = await service.export();

      expect(result).toEqual([
        { name: 'Config 1', filters: { page: 1 }, watched: false, statistics: true, pinned: false }
      ]);
    });

    it('should fallback to localStorage if backend export fails', async () => {
      const localStorageConfigs = [
        { name: 'Local', filters: {}, watched: false }
      ];
      vi.mocked(filterConfigsApi.getAll).mockRejectedValue(new Error('Network error'));
      vi.mocked(persistenceApi.getValue).mockResolvedValue(localStorageConfigs);

      const result = await service.export();

      expect(result).toEqual(localStorageConfigs);
    });
  });
});
