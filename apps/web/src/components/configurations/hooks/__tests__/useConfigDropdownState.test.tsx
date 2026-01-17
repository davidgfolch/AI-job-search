import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useConfigDropdownState } from '../useConfigDropdownState';

describe('useConfigDropdownState', () => {
  it('should initialize with empty configName and closed state', () => {
    const { result } = renderHook(() => useConfigDropdownState(''));
    expect(result.current.configName).toBe('');
    expect(result.current.isOpen).toBe(false);
  });

  it('should open dropdown and update configName on handleChange', () => {
    const { result } = renderHook(() => useConfigDropdownState(''));
    act(() => {
      result.current.handleChange({ target: { value: 'test' } } as any);
    });
    expect(result.current.configName).toBe('test');
    expect(result.current.isOpen).toBe(true);
  });

  it('should clear configName on focus if it matches savedConfigName', () => {
    const { result, rerender } = renderHook(
      ({ saved }) => useConfigDropdownState(saved),
      { initialProps: { saved: 'saved' } }
    );
    act(() => {
      result.current.setConfigName('saved');
    });
    act(() => {
      result.current.handleFocus();
    });
    expect(result.current.configName).toBe('');
    expect(result.current.isOpen).toBe(true);
  });

  it('should restore savedConfigName on blur if configName is empty', async () => {
    const { result } = renderHook(() => useConfigDropdownState('saved'));
    act(() => {
      result.current.handleBlur();
    });
    await new Promise(resolve => setTimeout(resolve, 250));
    expect(result.current.configName).toBe('saved');
    expect(result.current.isOpen).toBe(false);
  });
});
