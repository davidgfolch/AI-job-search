import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useFilterConfigurations } from '../useFilterConfigurations';
import { persistenceApi } from '../../../../api/persistence';

// Mock dependencies
vi.mock('../../../../api/persistence', () => ({
    persistenceApi: {
        getValue: vi.fn(),
        setValue: vi.fn(),
    }
}));

vi.mock('../../../../data/defaults', () => ({
    defaultFilterConfigurations: []
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
        (persistenceApi.getValue as any).mockResolvedValue([]);
        (persistenceApi.setValue as any).mockResolvedValue(true);
    });

    it('should load saved configs on mount', async () => {
        const savedConfigs = [{ name: 'Saved 1', filters: mockFilters }];
        (persistenceApi.getValue as any).mockResolvedValue(savedConfigs);

        const { result } = renderHook(() => useFilterConfigurations(defaultProps));

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
            expect(result.current.filteredConfigs[0].name).toBe('Saved 1');
        });
    });

    it('should save a new configuration', async () => {
        const { result } = renderHook(() => useFilterConfigurations(defaultProps));

        // Wait for initial load
        await waitFor(() => expect(persistenceApi.getValue).toHaveBeenCalled());

        act(() => {
            // Type the name
            result.current.handleChange({ target: { value: 'New Config' } } as any);
        });

        await act(async () => {
             await result.current.saveConfiguration();
        });

        expect(persistenceApi.setValue).toHaveBeenCalledWith(
            'filter_configurations',
            expect.arrayContaining([
                expect.objectContaining({ name: 'New Config', filters: mockFilters })
            ])
        );

        // Should update internal state
        expect(result.current.filteredConfigs).toHaveLength(1);
        expect(result.current.filteredConfigs[0].name).toBe('New Config');
        expect(result.current.configName).toBe(''); // Resets after save
    });

    it('should delete a configuration', async () => {
        const savedConfigs = [{ name: 'To Delete', filters: mockFilters }];
        (persistenceApi.getValue as any).mockResolvedValue(savedConfigs);

        const { result } = renderHook(() => useFilterConfigurations(defaultProps));

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
        });

        const stopPropagation = vi.fn();
        
        // Trigger delete
        act(() => {
            result.current.deleteConfiguration('To Delete', { stopPropagation } as any);
        });

        // Should open confirmation modal
        expect(result.current.confirmModal.isOpen).toBe(true);

        // Confirm delete
        await act(async () => {
            result.current.confirmModal.onConfirm();
        });

        expect(persistenceApi.setValue).toHaveBeenCalledWith('filter_configurations', []);
        expect(result.current.filteredConfigs).toHaveLength(0);
    });

    it('should reset missing filters when loading configuration', async () => {
        const savedFilters = { search: 'saved' }; // days_old missing
        const savedConfigs = [{ name: 'Saved 1', filters: savedFilters }];
        (persistenceApi.getValue as any).mockResolvedValue(savedConfigs);

        const { result } = renderHook(() => useFilterConfigurations(defaultProps));

        await waitFor(() => {
            expect(result.current.filteredConfigs).toHaveLength(1);
        });

        act(() => {
            result.current.loadConfiguration(savedConfigs[0] as any);
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
});
