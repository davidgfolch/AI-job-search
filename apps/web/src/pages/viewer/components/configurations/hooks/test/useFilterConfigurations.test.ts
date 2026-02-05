import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useFilterConfigurations } from '../useFilterConfigurations';
import { persistenceApi as commonPersistenceApi } from "../../../../../common/api/CommonPersistenceApi";
import { filterConfigsApi } from '../../../../api/FilterConfigurationsApi';
import { createWrapper, setupMocks } from './testHelpers';

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
    const defaultProps = {
        currentFilters: mockFilters as any,
        onLoadConfig: vi.fn(),
        onMessage: vi.fn(),
        additionalDefaults: []
    };

    beforeEach(() => {
        vi.clearAllMocks();
        setupMocks();
        (commonPersistenceApi.getValue as any).mockResolvedValue([]);
        (commonPersistenceApi.setValue as any).mockResolvedValue(true);
        (filterConfigsApi.getAll as any).mockResolvedValue([]);
        (filterConfigsApi.create as any).mockResolvedValue({ id: 1, name: 'test', filters: mockFilters, notify: false, created: new Date().toISOString(), modified: null });
        (filterConfigsApi.update as any).mockResolvedValue({ id: 1, name: 'test', filters: mockFilters, notify: false, created: new Date().toISOString(), modified: null });
        (filterConfigsApi.delete as any).mockResolvedValue(undefined);
    });

    it('should load saved configs on mount', async () => {
        const backendConfigs = [{
            id: 1,
            name: 'Saved 1',
            filters: mockFilters,
            notify: false,
            created: new Date().toISOString(),
            modified: null
        }];
        (filterConfigsApi.getAll as any).mockResolvedValue(backendConfigs);

        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper: createWrapper() });

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
            expect(result.current.filteredConfigs[0].name).toBe('Saved 1');
        });
    });

    it('should save a new configuration', async () => {
        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper: createWrapper() });

        await waitFor(() => expect(filterConfigsApi.getAll).toHaveBeenCalled());

        act(() => {
            result.current.handleChange({ target: { value: 'New Config' } } as any);
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
        expect(result.current.configName).toBe('');
    });

    it('should delete a configuration', async () => {
        const backendConfigs = [{
            id: 1,
            name: 'To Delete',
            filters: mockFilters,
            notify: false,
            created: new Date().toISOString(),
            modified: null
        }];
        (filterConfigsApi.getAll as any).mockResolvedValue(backendConfigs);

        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper: createWrapper() });

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
        });

        const stopPropagation = vi.fn();
        
        act(() => {
            result.current.deleteConfiguration('To Delete', { stopPropagation } as any);
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
        const backendConfigs = [{
            id: 1,
            name: 'Saved 1',
            filters: savedFilters,
            notify: false,
            created: new Date().toISOString(),
            modified: null
        }];
        (filterConfigsApi.getAll as any).mockResolvedValue(backendConfigs);

        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper: createWrapper() });

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
        });

        act(() => {
            result.current.loadConfiguration({ 
                name: backendConfigs[0].name, 
                filters: backendConfigs[0].filters,
                notify: backendConfigs[0].notify 
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
        const backendConfigs = [{
            id: 123,
            name: 'Stats Config',
            filters: mockFilters,
            notify: false,
            statistics: true,
            created: new Date().toISOString(),
            modified: null
        }];
        (filterConfigsApi.getAll as any).mockResolvedValue(backendConfigs);

        const { result } = renderHook(() => useFilterConfigurations(defaultProps), { wrapper: createWrapper() });

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
