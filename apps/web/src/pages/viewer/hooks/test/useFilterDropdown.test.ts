import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useFilterDropdown } from '../useFilterDropdown';

describe('useFilterDropdown', () => {
  const mockProps = {
    configs: [
      { name: 'Config A', filters: {} },
      { name: 'Config B', filters: {} },
      { name: 'Config C', filters: {} },
    ],
    configName: '',
    onLoad: vi.fn(),
    onSave: vi.fn(),
    onDelete: vi.fn(),
    setIsOpen: vi.fn(),
    isOpen: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('filters configs based on configName', () => {
    const { result } = renderHook(() => 
      useFilterDropdown({ ...mockProps, configName: 'B' })
    );
    expect(result.current.filteredConfigs).toHaveLength(1);
    expect(result.current.filteredConfigs[0].name).toBe('Config B');
  });

  it('navigates with arrow keys', () => {
    const { result } = renderHook(() => useFilterDropdown(mockProps));
    
    // Arrow Down
    act(() => {
      result.current.handleKeyDown({ key: 'ArrowDown', preventDefault: vi.fn() } as any);
    });
    expect(result.current.highlightIndex).toBe(0);
    
    act(() => {
      result.current.handleKeyDown({ key: 'ArrowDown', preventDefault: vi.fn() } as any);
    });
    expect(result.current.highlightIndex).toBe(1);

    // Arrow Up
    act(() => {
        result.current.handleKeyDown({ key: 'ArrowUp', preventDefault: vi.fn() } as any);
    });
    expect(result.current.highlightIndex).toBe(0);
  });

  it('loads config on Enter when highlighted', () => {
    const { result } = renderHook(() => useFilterDropdown(mockProps));
    
    // Highlight index 0 (Config A)
    act(() => {
        result.current.setHighlightIndex(0);
    });
    
    act(() => {
      result.current.handleKeyDown({ key: 'Enter', preventDefault: vi.fn() } as any);
    });
    
    expect(mockProps.onLoad).toHaveBeenCalledWith(mockProps.configs[0]);
    expect(mockProps.onSave).not.toHaveBeenCalled();
  });

  it('calls onSave on Enter when nothing highlighted', () => {
    const { result } = renderHook(() => useFilterDropdown(mockProps));
    
    act(() => {
      result.current.handleKeyDown({ key: 'Enter', preventDefault: vi.fn() } as any);
    });
    
    expect(mockProps.onSave).toHaveBeenCalled();
    expect(mockProps.onLoad).not.toHaveBeenCalled();
  });

  it('calls onDelete on Delete key', () => {
    const { result } = renderHook(() => useFilterDropdown(mockProps));
    const event = { key: 'Delete', preventDefault: vi.fn() } as any;
    
    act(() => {
        result.current.setHighlightIndex(1); // Config B
    });
    
    act(() => {
      result.current.handleKeyDown(event);
    });
    
    expect(mockProps.onDelete).toHaveBeenCalledWith('Config B', event);
  });
});
