import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useAutoResizeTextArea } from '../useAutoResizeTextArea';
import { createRef } from 'react';

describe('useAutoResizeTextArea', () => {
  let mockElement: HTMLTextAreaElement;
  let ref: React.RefObject<HTMLTextAreaElement>;

  beforeEach(() => {
    // Mock IntersectionObserver
    window.IntersectionObserver = class IntersectionObserver {
      constructor(_callback: any, _options: any) {}
      observe() {}
      unobserve() {}
      disconnect() {}
    } as any;

    mockElement = document.createElement('textarea');
    Object.defineProperty(mockElement, 'scrollHeight', {
      configurable: true,
      get: () => 100,
    });
    ref = { current: mockElement };
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
    // Clean up global mock if needed
    // @ts-ignore
    delete window.IntersectionObserver;
  });

  it('sets textarea height based on scrollHeight', () => {
    renderHook(() => useAutoResizeTextArea(ref, 'test value'));
    expect(mockElement.style.height).toBe('105px');
  });

  it('updates height when value changes', () => {
    const { rerender } = renderHook(
      ({ value }) => useAutoResizeTextArea(ref, value),
      { initialProps: { value: 'initial' } }
    );
    const initialHeight = mockElement.style.height;
    Object.defineProperty(mockElement, 'scrollHeight', {
      configurable: true,
      get: () => 200,
    });
    rerender({ value: 'new much longer value' });
    expect(mockElement.style.height).not.toBe(initialHeight);
  });

  it('handles null ref gracefully', () => {
    const nullRef = createRef<HTMLTextAreaElement>();
    expect(() => {
      renderHook(() => useAutoResizeTextArea(nullRef, 'test'));
    }).not.toThrow();
  });

  it('cleans up event listeners on unmount', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');
    const { unmount } = renderHook(() => useAutoResizeTextArea(ref, 'test'));
    unmount();
    expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function));
  });
});
