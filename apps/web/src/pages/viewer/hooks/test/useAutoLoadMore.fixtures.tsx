import { render, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useRef } from 'react';
import { useAutoLoadMore } from '../useAutoLoadMore';

export interface HarnessProps {
    itemCount?: number;
    hasMore?: boolean;
    isLoading?: boolean;
    onLoadMore?: () => void;
}

export const Harness = ({ itemCount = 1, hasMore = true, isLoading = false, onLoadMore }: HarnessProps) => {
    const contentRef = useRef<HTMLTableElement>(null);
    const sentinelRef = useRef<HTMLDivElement>(null);
    useAutoLoadMore({ contentRef, sentinelRef, itemCount, hasMore, isLoading, onLoadMore });
    return (
        <div data-testid="container">
            <table ref={contentRef}><tbody><tr /></tbody></table>
            <div ref={sentinelRef} data-testid="sentinel" />
        </div>
    );
};

/** Places the end of the list `bottom` pixels from the top of the viewport. */
export const setSentinelRect = (sentinel: HTMLElement, { bottom, width, height }: { bottom: number; width: number; height: number }) => {
    sentinel.getBoundingClientRect = () => ({ bottom, width, height, top: bottom - height, left: 0, right: width, x: 0, y: bottom - height, toJSON: () => ({}) }) as DOMRect;
};

export const setSentinelBottom = (sentinel: HTMLElement, bottom: number) => setSentinelRect(sentinel, { bottom, width: 100, height: 1 });
export const hideSentinel = (sentinel: HTMLElement) => setSentinelRect(sentinel, { bottom: 0, width: 0, height: 0 });

export const setWindowHeight = (height: number) => Object.defineProperty(window, 'innerHeight', { value: height, configurable: true });

export const ON_SCREEN_BOTTOM = 500;
export const OFF_SCREEN_BOTTOM = 5000;
export const VIEWPORT_HEIGHT = 1000;

let intersectionCallbacks: IntersectionObserverCallback[] = [];
let resizeCallbacks: ResizeObserverCallback[] = [];

export const installObserverMocks = () => {
    intersectionCallbacks = [];
    globalThis.IntersectionObserver = vi.fn(function(this: IntersectionObserver, callback: IntersectionObserverCallback) {
        intersectionCallbacks.push(callback);
        return { observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn(), root: null, rootMargin: '', thresholds: [], takeRecords: () => [] };
    }) as any;
    resizeCallbacks = [];
    globalThis.ResizeObserver = vi.fn(function(this: ResizeObserver, callback: ResizeObserverCallback) {
        resizeCallbacks.push(callback);
        return { observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() };
    }) as any;
};

export const flushFrames = async () => {
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 50)); });
};

export const fireIntersection = (isIntersecting: boolean) => {
    act(() => { intersectionCallbacks.forEach(cb => cb([{ isIntersecting } as IntersectionObserverEntry], {} as IntersectionObserver)); });
};

export const fireResize = async () => {
    act(() => { resizeCallbacks.forEach(cb => cb([], {} as ResizeObserver)); });
    await flushFrames();
};

export const fireScroll = async () => {
    act(() => { window.dispatchEvent(new Event('scroll')); });
    await flushFrames();
};

/** Renders the harness with the end of the list placed on screen. */
export const renderOnScreen = (props: HarnessProps) => {
    const result = render(<Harness {...props} />);
    setSentinelBottom(result.getByTestId('sentinel'), ON_SCREEN_BOTTOM);
    return result;
};

/** Renders the harness with the end of the list below the fold. */
export const renderOffScreen = (props: HarnessProps) => {
    const result = render(<Harness {...props} />);
    setSentinelBottom(result.getByTestId('sentinel'), OFF_SCREEN_BOTTOM);
    return result;
};
