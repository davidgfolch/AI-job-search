import { vi } from 'vitest';

export const setupIntersectionObserverMock = () => {
  const mockIntersectionObserver = vi.fn(function(this: IntersectionObserver, callback: IntersectionObserverCallback) {
    return {
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
      root: null,
      rootMargin: '',
      thresholds: [],
      takeRecords: () => [],
    };
  }) as any;

  globalThis.IntersectionObserver = mockIntersectionObserver;
  return mockIntersectionObserver;
};

export const setupResizeObserverMock = () => {
  const mockResizeObserver = vi.fn(function(this: ResizeObserver, callback: ResizeObserverCallback) {
    return {
      observe: vi.fn(),
      unobserve: vi.fn(),
      disconnect: vi.fn(),
    };
  }) as any;

  globalThis.ResizeObserver = mockResizeObserver;
  return mockResizeObserver;
};

export const setupScrollIntoViewMock = () => {
  Element.prototype.scrollIntoView = vi.fn();
};

export const setupElementSizeMocks = () => {
  Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
    configurable: true,
    value: 100,
  });
  
  Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
    configurable: true,
    value: 100,
  });
};

export const setupDOMMocks = () => {
  setupIntersectionObserverMock();
  setupResizeObserverMock();
  setupScrollIntoViewMock();
  setupElementSizeMocks();
};

export const cleanupDOMMocks = () => {
  vi.unstubAllGlobals();
};