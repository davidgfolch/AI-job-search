import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useConfigOperations } from '../useConfigOperations';
import type { FilterConfig } from '../useFilterConfigurations';

describe('useConfigOperations - saveConfiguration', () => {
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

    it('saves configuration successfully', async () => {
        const props = createProps();
        const { result } = renderHook(() => useConfigOperations(props));
        
        await act(async () => {
            await result.current.saveConfiguration();
        });

        expect(props.service.save).toHaveBeenCalled();
        expect(props.setSavedConfigs).toHaveBeenCalled();
        expect(props.setConfigName).toHaveBeenCalledWith('');
        expect(props.setIsOpen).toHaveBeenCalledWith(false);
        expect(props.notify).toHaveBeenCalledWith('Configuration "Test Config" saved!', 'success');
    });

    it('shows error when config name is empty', async () => {
        const props = createProps({}, { configName: '   ' });
        const { result } = renderHook(() => useConfigOperations(props));

        await act(async () => {
            await result.current.saveConfiguration();
        });

        expect(props.notify).toHaveBeenCalledWith('Please enter a name for the configuration', 'error');
        expect(props.service.save).not.toHaveBeenCalled();
    });

    it('overwrites existing config with same name', async () => {
        const existingConfigs: FilterConfig[] = [
            { name: 'Test Config', filters: { search: 'old' }, watched: false, statistics: true, pinned: false, ordering: 0, created: '', modified: null },
        ];
        const props = createProps({}, { savedConfigs: existingConfigs, currentFilters: { search: 'new' } });
        const { result } = renderHook(() => useConfigOperations(props));

        await act(async () => {
            await result.current.saveConfiguration();
        });

        const savedConfigs = props.setSavedConfigs.mock.calls[0][0];
        expect(savedConfigs[0].name).toBe('Test Config');
        expect(savedConfigs[0].filters.search).toBe('new');
    });

    it('notifies on save failure', async () => {
        const mockSave = vi.fn().mockRejectedValue(new Error('Save failed'));
        const props = createProps({ save: mockSave });
        const { result } = renderHook(() => useConfigOperations(props));

        await act(async () => {
            await result.current.saveConfiguration();
        });

        expect(props.notify).toHaveBeenCalledWith('Failed to save configuration', 'error');
    });
});
