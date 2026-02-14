import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useConfigOperations } from '../useConfigOperations';
import type { FilterConfig } from '../useFilterConfigurations';

describe('useConfigOperations - reorderConfigurations', () => {
    const createMockService = (overrides = {}) => ({
        save: vi.fn().mockResolvedValue(undefined),
        export: vi.fn().mockResolvedValue([]),
        load: vi.fn().mockResolvedValue([]),
        ...overrides,
    });

    const createProps = (serviceOverrides = {}, propsOverrides = {}) => ({
        service: createMockService(serviceOverrides),
        savedConfigs: [] as FilterConfig[],
        setSavedConfigs: vi.fn(),
        currentFilters: { search: 'test' },
        configName: 'Test Config',
        setConfigName: vi.fn(),
        setIsOpen: vi.fn(),
        setSavedConfigName: vi.fn(),
        onLoadConfig: vi.fn(),
        notify: vi.fn(),
        confirmModal: {
            confirm: vi.fn(),
            isOpen: false,
            message: '',
            close: vi.fn(),
            handleConfirm: vi.fn(),
        },
        ...propsOverrides,
    });

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('reorders configurations successfully', async () => {
        const configs: FilterConfig[] = [
            { name: 'A', filters: {}, watched: false, statistics: true, pinned: false, ordering: 0, created: '', modified: null },
            { name: 'B', filters: {}, watched: false, statistics: true, pinned: false, ordering: 1, created: '', modified: null },
        ];
        const props = createProps();
        
        const { result } = renderHook(() => useConfigOperations(props));
        
        await act(async () => {
            await result.current.reorderConfigurations([configs[1], configs[0]]);
        });

        const savedConfigs = props.setSavedConfigs.mock.calls[0][0];
        expect(savedConfigs[0].ordering).toBe(0);
        expect(savedConfigs[1].ordering).toBe(1);
        expect(props.service.save).toHaveBeenCalled();
    });

    it('notifies on reorder failure', async () => {
        const mockSave = vi.fn().mockRejectedValue(new Error('Reorder failed'));
        const configs: FilterConfig[] = [
            { name: 'A', filters: {}, watched: false, statistics: true, pinned: false, ordering: 0, created: '', modified: null },
        ];
        const props = createProps({ save: mockSave });
        
        const { result } = renderHook(() => useConfigOperations(props));
        
        await act(async () => {
            await result.current.reorderConfigurations(configs);
        });

        expect(props.notify).toHaveBeenCalledWith('Failed to save new order', 'error');
    });
});
