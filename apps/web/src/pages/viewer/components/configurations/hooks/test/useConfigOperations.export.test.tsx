import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useConfigOperations } from '../useConfigOperations';
import type { FilterConfig } from '../useFilterConfigurations';

describe('useConfigOperations - exportToDefaults', () => {
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

    it('exports configurations successfully', async () => {
        const configs = [{ name: 'Test', filters: {} }];
        const props = createProps({ export: vi.fn().mockResolvedValue(configs) });
        
        const { result } = renderHook(() => useConfigOperations(props));
        
        await act(async () => {
            await result.current.exportToDefaults();
        });

        expect(props.service.export).toHaveBeenCalled();
        expect(props.notify).toHaveBeenCalledWith('Configuration downloaded!', 'success');
    });

    it('handles empty configurations', async () => {
        const props = createProps({ export: vi.fn().mockResolvedValue([]) });
        
        const { result } = renderHook(() => useConfigOperations(props));
        
        await act(async () => {
            await result.current.exportToDefaults();
        });

        expect(props.notify).toHaveBeenCalledWith('No configurations to export.', 'error');
    });

    it('handles undefined configurations', async () => {
        const props = createProps({ export: vi.fn().mockResolvedValue(null) });
        
        const { result } = renderHook(() => useConfigOperations(props));
        
        await act(async () => {
            await result.current.exportToDefaults();
        });

        expect(props.notify).toHaveBeenCalledWith('No configurations to export.', 'error');
    });

    it('notifies on export failure', async () => {
        const mockExport = vi.fn().mockRejectedValue(new Error('Export failed'));
        const props = createProps({ export: mockExport });
        
        const { result } = renderHook(() => useConfigOperations(props));
        
        await act(async () => {
            await result.current.exportToDefaults();
        });

        expect(props.notify).toHaveBeenCalledWith('Failed to copy to clipboard. Check console.', 'error');
    });
});
