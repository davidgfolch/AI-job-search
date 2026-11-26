import '@testing-library/jest-dom';
import { beforeEach, vi } from 'vitest';

// Polyfill ResizeObserver for jsdom
if (typeof global.ResizeObserver === 'undefined') {
    class ResizeObserver {
        callback: ResizeObserverCallback;
        constructor(callback: ResizeObserverCallback) {
            this.callback = callback;
        }
        observe(target: Element) {
            // Trigger callback immediately for testing
            this.callback([{ target, contentRect: { height: target.scrollHeight, width: target.clientWidth } }] as any, this);
        }
        unobserve() {}
        disconnect() {}
    }
    global.ResizeObserver = ResizeObserver as any;
}

// Polyfill IntersectionObserver for jsdom
if (typeof global.IntersectionObserver === 'undefined') {
    class IntersectionObserver {
        callback: IntersectionObserverCallback;
        constructor(callback: IntersectionObserverCallback) {
            this.callback = callback;
        }
        observe() {}
        unobserve() {}
        disconnect() {}
    }
    global.IntersectionObserver = IntersectionObserver as any;
}

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

beforeEach(() => {
    window.localStorage.clear();
});
