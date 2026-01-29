import '@testing-library/jest-dom';
import { beforeEach } from 'vitest';

const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: (key: string) => store[key] || null,
        setItem: (key: string, value: string) => {
            store[key] = value.toString();
        },
        clear: () => {
            store = {};
        },
        removeItem: (key: string) => {
            delete store[key];
        }
    };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// Clean up after each test
beforeEach(() => {
    window.localStorage.clear();
});
