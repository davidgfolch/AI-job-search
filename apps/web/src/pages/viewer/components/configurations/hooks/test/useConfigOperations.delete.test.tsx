import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useConfigOperations } from '../useConfigOperations';
import type { FilterConfig } from '../useFilterConfigurations';

describe('useConfigOperations - deleteConfiguration', () => {
    const mockConfirmModal = {
        confirm: vi.fn(),
        isOpen: false,
        message: '',
        close: vi.fn(),
        handleConfirm: vi.fn(),
    };

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
        confirmModal: mockConfirmModal,
        ...propsOverrides,
    });

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('opens confirmation modal', () => {
        const props = createProps();
        const { result } = renderHook(() => useConfigOperations(props));

        result.current.deleteConfiguration('Test Config', { stopPropagation: vi.fn() } as any);

        expect(mockConfirmModal.confirm).toHaveBeenCalledWith(
            'Delete configuration "Test Config"?',
            expect.any(Function)
        );
    });

    it('deletes config when confirmed', async () => {
        const existingConfigs: FilterConfig[] = [
            { name: 'Test Config', filters: {}, watched: false, statistics: true, pinned: false, ordering: 0, created: '', modified: null },
            { name: 'Other', filters: {}, watched: false, statistics: true, pinned: false, ordering: 1, created: '', modified: null },
        ];
        const props = createProps({}, { savedConfigs: existingConfigs });
        const { result } = renderHook(() => useConfigOperations(props));

        result.current.deleteConfiguration('Test Config', { stopPropagation: vi.fn() } as any);
        
        const confirmCallback = mockConfirmModal.confirm.mock.calls[0][1];
        await act(async () => {
            await confirmCallback();
        });

        expect(props.service.save).toHaveBeenCalled();
        expect(props.setSavedConfigs).toHaveBeenCalledWith(
            expect.arrayContaining([
                expect.not.objectContaining({ name: 'Test Config' })
            ])
        );
    });

    it('clears config name when deleting current config', async () => {
        const existingConfigs: FilterConfig[] = [
            { name: 'Current Config', filters: {}, watched: false, statistics: true, pinned: false, ordering: 0, created: '', modified: null },
        ];
        const props = createProps({}, { savedConfigs: existingConfigs, configName: 'Current Config' });
        const { result } = renderHook(() => useConfigOperations(props));

        result.current.deleteConfiguration('Current Config', { stopPropagation: vi.fn() } as any);
        
        const confirmCallback = mockConfirmModal.confirm.mock.calls[0][1];
        await act(async () => {
            await confirmCallback();
        });

        expect(props.setConfigName).toHaveBeenCalledWith('');
        expect(props.setSavedConfigName).toHaveBeenCalledWith('');
    });

    it('notifies on delete failure', async () => {
        const mockSave = vi.fn().mockRejectedValue(new Error('Delete failed'));
        const props = createProps({ save: mockSave });
        const { result } = renderHook(() => useConfigOperations(props));

        result.current.deleteConfiguration('Test Config', { stopPropagation: vi.fn() } as any);
        
        const confirmCallback = mockConfirmModal.confirm.mock.calls[0][1];
        await act(async () => {
            await confirmCallback();
        });

        expect(props.notify).toHaveBeenCalledWith('Failed to delete configuration', 'error');
    });
});
