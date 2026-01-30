import { vi } from 'vitest';

export const mockLocalStorage = () => {
  const store: Record<string, string> = {};
  
  const mockItem = {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
        for (const key in store) delete store[key];
    }),
    length: 0,
    key: vi.fn(),
  };

  Object.defineProperty(window, 'localStorage', {
    value: mockItem,
    writable: true
  });

  return mockItem;
};
