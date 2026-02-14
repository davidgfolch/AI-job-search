import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useConfigOperations } from '../useConfigOperations';
import type { FilterConfig } from '../useFilterConfigurations';

describe('useConfigOperations - loadConfiguration', () => {
    const createMockService = (overrides = {}) => ({
        save: vi.fn().mockResolvedValue(undefined),
        export: vi.fn().mockResolvedValue([]),
        load: vi.fn().mockResolvedValue([]),
        ...overrides,
    });

    const createProps = (propsOverrides = {}) => ({
        service: createMockService(),
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

    it('loads configuration and closes dropdown', () => {
        const props = createProps();
        const config: FilterConfig = { name: 'Test', filters: { search: 'loaded' }, watched: false, statistics: true, pinned: false, ordering: 0, created: '', modified: null };
        const { result } = renderHook(() => useConfigOperations(props));

        result.current.loadConfiguration(config);

        expect(props.onLoadConfig).toHaveBeenCalledWith({ search: 'loaded' }, 'Test');
        expect(props.setConfigName).toHaveBeenCalledWith('Test');
        expect(props.setSavedConfigName).toHaveBeenCalledWith('Test');
        expect(props.setIsOpen).toHaveBeenCalledWith(false);
    });
});
