import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useFilterConfigurations } from '../useFilterConfigurations';
import { persistenceApi } from '../../../common/api/CommonPersistenceApi';
import { useConfirmationModal } from '../../../common/hooks/useConfirmationModal';
import { useFilterDropdown } from '../useFilterDropdown';

// Mock dependencies
vi.mock('../../../common/api/CommonPersistenceApi', () => ({
  persistenceApi: {
    getValue: vi.fn(),
    setValue: vi.fn(),
  }
}));

vi.mock('../../../common/hooks/useConfirmationModal', () => ({
  useConfirmationModal: vi.fn(),
}));

vi.mock('../useFilterDropdown', () => ({
  useFilterDropdown: vi.fn(),
}));

vi.mock('../../../common/api/defaults', () => ({
  defaultFilterConfigurations: [{ name: 'Default 1', filters: {} }],
  BOOLEAN_FILTERS: []
}));

vi.mock('../constants', () => ({
  BOOLEAN_FILTERS: [{ key: 'ignored'}, { key: 'seen' }]
}));

describe('useFilterConfigurations', () => {
  const mockProps = {
    currentFilters: { page: 1 },
    onLoadConfig: vi.fn(),
    onMessage: vi.fn(),
    additionalDefaults: [],
  };

  const mockConfirmModal = {
    isOpen: false,
    message: '',
    confirm: vi.fn(),
    close: vi.fn(),
    handleConfirm: vi.fn(),
  };

  const mockFilterDropdown = {
    highlightIndex: -1,
    setHighlightIndex: vi.fn(),
    wrapperRef: { current: null },
    filteredConfigs: [],
    handleKeyDown: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useConfirmationModal as any).mockReturnValue(mockConfirmModal);
    (useFilterDropdown as any).mockReturnValue(mockFilterDropdown);
  });

  it('loads configurations on mount', async () => {
    const storedConfigs = [{ name: 'Stored', filters: {} }];
    vi.mocked(persistenceApi.getValue).mockResolvedValue(storedConfigs);
    
    renderHook(() => useFilterConfigurations(mockProps));
    
    // Wait for effect
    await waitFor(() => {
        // We can't easily check internal state without exposing it, 
        // but checking side effects or if it didn't crash is a start.
        // Actually, the hook is designed to pass configs to useFilterDropdown.
        expect(useFilterDropdown).toHaveBeenCalled();
    });
    
    // Check if useFilterDropdown was called with loaded configs
    const lastCall = (useFilterDropdown as any).mock.calls.slice(-1)[0][0];
    expect(lastCall.configs).toHaveLength(2); // Stored + Default 1
    expect(lastCall.configs).toEqual(expect.arrayContaining([
        expect.objectContaining({ name: 'Stored' }),
        expect.objectContaining({ name: 'Default 1' })
    ]));
  });

  it('saves configuration successfully', async () => {
    vi.mocked(persistenceApi.getValue).mockResolvedValue([]);
    vi.mocked(persistenceApi.setValue).mockResolvedValue(undefined);
    
    const { result } = renderHook(() => useFilterConfigurations(mockProps));
    
    // Simulate typing name
    act(() => {
        result.current.handleChange({ target: { value: 'New Config' } } as any);
    });
    
    await act(async () => {
       await result.current.saveConfiguration();
    });
    
    expect(persistenceApi.setValue).toHaveBeenCalledWith(
        'filter_configurations',
        expect.arrayContaining([expect.objectContaining({ name: 'New Config' })])
    );
    expect(mockProps.onMessage).toHaveBeenCalledWith(expect.stringContaining('saved'), 'success');
  });

  it('handles validation error when saving with empty name', async () => {
    const { result } = renderHook(() => useFilterConfigurations(mockProps));
    
    await waitFor(() => expect(persistenceApi.getValue).toHaveBeenCalled());

    await act(async () => {
       await result.current.saveConfiguration();
    });
    
    expect(persistenceApi.setValue).not.toHaveBeenCalled();
    expect(mockProps.onMessage).toHaveBeenCalledWith(expect.stringContaining('enter a name'), 'error');
  });

  it('loads configuration', async () => {
    const { result } = renderHook(() => useFilterConfigurations(mockProps));
    await waitFor(() => expect(persistenceApi.getValue).toHaveBeenCalled());

    const config = { name: 'Test', filters: { search: 'ABC' } };
    
    act(() => {
        result.current.loadConfiguration(config);
    });
    
    expect(mockProps.onLoadConfig).toHaveBeenCalledWith(config.filters, config.name);
    // Should verify it sets configName
    expect(result.current.configName).toBe('Test');
  });

  it('deletes configuration', async () => {
     const { result } = renderHook(() => useFilterConfigurations(mockProps));
     await waitFor(() => expect(persistenceApi.getValue).toHaveBeenCalled());

     const event = { stopPropagation: vi.fn() } as any;
     
     act(() => {
         result.current.deleteConfiguration('Test Config', event);
     });
     
     expect(mockConfirmModal.confirm).toHaveBeenCalledWith(
         expect.stringContaining('Delete configuration "Test Config"?'),
         expect.any(Function)
     );
     
     // Simulate confirm callback execution
     const confirmCallback = mockConfirmModal.confirm.mock.calls[0][1];
     await act(async () => {
         await confirmCallback();
     });
     
     expect(persistenceApi.setValue).toHaveBeenCalled();
  });
});
