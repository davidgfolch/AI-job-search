import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useFilterConfigurations } from '../useFilterConfigurations';
import { persistenceApi as commonPersistenceApi } from "../../../../../common/api/CommonPersistenceApi";
import { filterConfigsApi, type FilterConfiguration } from '../../../../api/FilterConfigurationsApi';
import { createWrapper } from './testHelpers';
import type { JobListParams } from '../../../../api/ViewerApi';

vi.mock('../../../../../common/api/CommonPersistenceApi', () => ({
    persistenceApi: {
        getValue: vi.fn(),
        setValue: vi.fn(),
    }
}));

vi.mock('../../../../api/FilterConfigurationsApi', () => ({
    filterConfigsApi: {
        getAll: vi.fn(),
        create: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
    }
}));

vi.mock('../../../../../../resources/defaultFilterConfigurations.json', () => ({
    default: []
}));

describe('useFilterConfigurations', () => {
    const mockFilters = { search: 'test', employment_type: [], remote: null, posted_at: null };
    const makeConfig = (over: Partial<FilterConfiguration> = {}): FilterConfiguration => ({
        id: 1, name: 'test', filters: mockFilters as unknown as JobListParams, watched: false,
        statistics: false, pinned: false, ordering: 0, created: new Date().toISOString(), modified: null, ...over
    });
    const defaultProps = {
        currentFilters: mockFilters as unknown as JobListParams,
        onLoadConfig: vi.fn(),
        onMessage: vi.fn(),
        additionalDefaults: []
    };

    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(commonPersistenceApi.getValue).mockResolvedValue([]);
        vi.mocked(commonPersistenceApi.setValue).mockResolvedValue(undefined);
        vi.mocked(filterConfigsApi.getAll).mockResolvedValue([]);
        vi.mocked(filterConfigsApi.create).mockResolvedValue(makeConfig());
        vi.mocked(filterConfigsApi.update).mockResolvedValue(makeConfig());
        vi.mocked(filterConfigsApi.delete).mockResolvedValue(undefined);
    });

    it('should load saved configs on mount', async () => {
        const backendConfigs = [makeConfig({ name: 'Saved 1' })];
        vi.mocked(filterConfigsApi.getAll).mockResolvedValue(backendConfigs);

        const { wrapper } = createWrapper();
        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper });

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
            expect(result.current.filteredConfigs[0].name).toBe('Saved 1');
        });
    });

    it('should save a new configuration', async () => {
        const { wrapper } = createWrapper();
        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper });

        await waitFor(() => expect(filterConfigsApi.getAll).toHaveBeenCalled());

        act(() => {
            result.current.handleChange({ target: { value: 'New Config' } } as React.ChangeEvent<HTMLInputElement>);
        });

        await act(async () => {
             await result.current.saveConfiguration();
        });

        expect(filterConfigsApi.create).toHaveBeenCalledWith(
            expect.objectContaining({ 
                name: 'New Config', 
                filters: mockFilters 
            })
        );

        expect(result.current.filteredConfigs).toHaveLength(1);
        expect(result.current.filteredConfigs[0].name).toBe('New Config');
        expect(result.current.configName).toBe('New Config');
        expect(result.current.savedConfigName).toBe('New Config');
    });

    it('should delete a configuration', async () => {
        const backendConfigs = [makeConfig({ name: 'To Delete' })];
        vi.mocked(filterConfigsApi.getAll).mockResolvedValue(backendConfigs);

        const { wrapper } = createWrapper();
        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper });

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
        });

        const stopPropagation = vi.fn();
        
        act(() => {
            result.current.deleteConfiguration('To Delete', { stopPropagation } as unknown as React.SyntheticEvent);
        });

        expect(result.current.confirmModal.isOpen).toBe(true);

        await act(async () => {
            result.current.confirmModal.onConfirm();
        });

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(0);
        });
    });

    it('should reset missing filters when loading configuration', async () => {
        const savedFilters = { search: 'saved' };
        const backendConfigs = [makeConfig({ name: 'Saved 1', filters: savedFilters })];
        vi.mocked(filterConfigsApi.getAll).mockResolvedValue(backendConfigs);

        const { wrapper } = createWrapper();
        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper });

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
        });

        act(() => {
            result.current.loadConfiguration({ 
                name: backendConfigs[0].name, 
                filters: backendConfigs[0].filters,
                watched: backendConfigs[0].watched 
            });
        });

        // onLoadConfig should be called with normalized filters
        expect(defaultProps.onLoadConfig).toHaveBeenCalledWith(
            expect.objectContaining({
                search: 'saved',
                days_old: undefined
            }),
            'Saved 1'
        );
    });
    
    it('should update statistics setting using single API call', async () => {
        const backendConfigs = [makeConfig({ id: 123, name: 'Stats Config', statistics: true })];
        vi.mocked(filterConfigsApi.getAll).mockResolvedValue(backendConfigs);

        const { wrapper } = createWrapper();
        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper });

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
        });

        // Initial state
        expect(result.current.filteredConfigs[0].statistics).toBe(true);

        // Toggle statistics
        await act(async () => {
            await result.current.toggleStatistics('Stats Config');
        });

        // Verify API was called with just the ID and the new value
        expect(filterConfigsApi.update).toHaveBeenCalledWith(123, { statistics: false });
        
        // Verify local state updated
        expect(result.current.filteredConfigs[0].statistics).toBe(false);
    });
});
