import { render, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useRef } from 'react';
import { useAutoLoadMore } from '../useAutoLoadMore';

interface HarnessProps {
    itemCount?: number;
    hasMore?: boolean;
    isLoading?: boolean;
    onLoadMore?: () => void;
}

const Harness = ({ itemCount = 1, hasMore = true, isLoading = false, onLoadMore }: HarnessProps) => {
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
const setSentinelRect = (sentinel: HTMLElement, { bottom, width, height }: { bottom: number; width: number; height: number }) => {
    sentinel.getBoundingClientRect = () => ({ bottom, width, height, top: bottom - height, left: 0, right: width, x: 0, y: bottom - height, toJSON: () => ({}) }) as DOMRect;
};

const setSentinelBottom = (sentinel: HTMLElement, bottom: number) => setSentinelRect(sentinel, { bottom, width: 100, height: 1 });
const hideSentinel = (sentinel: HTMLElement) => setSentinelRect(sentinel, { bottom: 0, width: 0, height: 0 });

const setWindowHeight = (height: number) => Object.defineProperty(window, 'innerHeight', { value: height, configurable: true });

const ON_SCREEN_BOTTOM = 500;
const OFF_SCREEN_BOTTOM = 5000;
const VIEWPORT_HEIGHT = 1000;

let intersectionCallbacks: IntersectionObserverCallback[] = [];
let resizeCallbacks: ResizeObserverCallback[] = [];

const installObserverMocks = () => {
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

const flushFrames = async () => {
    await act(async () => { await new Promise(resolve => setTimeout(resolve, 50)); });
};

const fireIntersection = (isIntersecting: boolean) => {
    act(() => { intersectionCallbacks.forEach(cb => cb([{ isIntersecting } as IntersectionObserverEntry], {} as IntersectionObserver)); });
};

const fireResize = async () => {
    act(() => { resizeCallbacks.forEach(cb => cb([], {} as ResizeObserver)); });
    await flushFrames();
};

const fireScroll = async () => {
    act(() => { window.dispatchEvent(new Event('scroll')); });
    await flushFrames();
};

/** Renders the harness with the end of the list placed on screen. */
const renderOnScreen = (props: HarnessProps) => {
    const result = render(<Harness {...props} />);
    setSentinelBottom(result.getByTestId('sentinel'), ON_SCREEN_BOTTOM);
    return result;
};

/** Renders the harness with the end of the list below the fold. */
const renderOffScreen = (props: HarnessProps) => {
    const result = render(<Harness {...props} />);
    setSentinelBottom(result.getByTestId('sentinel'), OFF_SCREEN_BOTTOM);
    return result;
};

describe('useAutoLoadMore', () => {
    beforeEach(() => {
        installObserverMocks();
        setWindowHeight(VIEWPORT_HEIGHT);
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('requests the next page when the end of the list is already on screen', async () => {
        const onLoadMore = vi.fn();
        renderOnScreen({ onLoadMore });

        await flushFrames();

        expect(onLoadMore).toHaveBeenCalledTimes(1);
    });

    it('does not request the next page when the end of the list is below the fold', async () => {
        const onLoadMore = vi.fn();
        renderOffScreen({ onLoadMore });

        await flushFrames();

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('does not request the next page while the list is hidden', async () => {
        const onLoadMore = vi.fn();
        const { getByTestId } = render(<Harness onLoadMore={onLoadMore} />);
        hideSentinel(getByTestId('sentinel'));

        await flushFrames();

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('does not request the next page when there are no further pages', async () => {
        const onLoadMore = vi.fn();
        renderOnScreen({ onLoadMore, hasMore: false });

        await flushFrames();

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('does not request the next page while a page is in flight', async () => {
        const onLoadMore = vi.fn();
        const { rerender } = renderOnScreen({ onLoadMore, isLoading: true });

        await flushFrames();
        fireIntersection(true);
        expect(onLoadMore).not.toHaveBeenCalled();

        rerender(<Harness onLoadMore={onLoadMore} isLoading={false} itemCount={21} />);
        await flushFrames();

        expect(onLoadMore).toHaveBeenCalledTimes(1);
    });

    it('keeps filling the list as appended pages still leave the end on screen', async () => {
        const onLoadMore = vi.fn();
        const { rerender } = renderOnScreen({ onLoadMore, itemCount: 20 });

        await flushFrames();
        expect(onLoadMore).toHaveBeenCalledTimes(1);

        rerender(<Harness onLoadMore={onLoadMore} itemCount={40} />);
        await flushFrames();
        expect(onLoadMore).toHaveBeenCalledTimes(2);
    });

    it('stops filling the list once the appended rows push the end off screen', async () => {
        const onLoadMore = vi.fn();
        const { getByTestId, rerender } = renderOnScreen({ onLoadMore, itemCount: 20 });

        await flushFrames();
        expect(onLoadMore).toHaveBeenCalledTimes(1);

        setSentinelBottom(getByTestId('sentinel'), OFF_SCREEN_BOTTOM);
        rerender(<Harness onLoadMore={onLoadMore} itemCount={40} />);
        await flushFrames();

        expect(onLoadMore).toHaveBeenCalledTimes(1);
    });

    it('requests the next page when the list grows back onto the screen', async () => {
        const onLoadMore = vi.fn();
        const { getByTestId } = renderOffScreen({ onLoadMore });

        await flushFrames();
        expect(onLoadMore).not.toHaveBeenCalled();

        // Taller window: the end of the list is visible again, so more rows are needed.
        setSentinelBottom(getByTestId('sentinel'), ON_SCREEN_BOTTOM);
        await fireResize();

        expect(onLoadMore).toHaveBeenCalledTimes(1);
    });

    it('does not request the next page on resize while the end of the list is off screen', async () => {
        const onLoadMore = vi.fn();
        renderOffScreen({ onLoadMore });

        await fireResize();

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('requests the next page when the end of the list is scrolled into view', () => {
        const onLoadMore = vi.fn();
        renderOffScreen({ onLoadMore });

        fireIntersection(false);
        expect(onLoadMore).not.toHaveBeenCalled();

        fireIntersection(true);
        expect(onLoadMore).toHaveBeenCalledTimes(1);
    });

    it('requests the next page on scroll, for browsers that miss the intersection change', async () => {
        const onLoadMore = vi.fn();
        const { getByTestId } = renderOffScreen({ onLoadMore });

        await fireScroll();
        expect(onLoadMore).not.toHaveBeenCalled();

        // Scrolling a nested container brings the end of the list within the prefetch margin.
        setSentinelBottom(getByTestId('sentinel'), VIEWPORT_HEIGHT + 100);
        await fireScroll();

        expect(onLoadMore).toHaveBeenCalledTimes(1);
    });

    it('does not request the next page on scroll while the end of the list stays far below', async () => {
        const onLoadMore = vi.fn();
        renderOffScreen({ onLoadMore });

        await fireScroll();

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('ignores scroll signals once the last page is loaded', async () => {
        const onLoadMore = vi.fn();
        const { getByTestId } = renderOffScreen({ onLoadMore, hasMore: false });
        setSentinelBottom(getByTestId('sentinel'), VIEWPORT_HEIGHT + 100);

        await fireScroll();

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('does not request the next page while an empty list is on screen', async () => {
        const onLoadMore = vi.fn();
        const { getByTestId } = render(<Harness onLoadMore={onLoadMore} itemCount={0} />);
        setSentinelBottom(getByTestId('sentinel'), ON_SCREEN_BOTTOM);

        await flushFrames();
        fireIntersection(true);

        expect(onLoadMore).not.toHaveBeenCalled();
    });

    it('requests the next page only once per displayed page', async () => {
        const onLoadMore = vi.fn();
        renderOnScreen({ onLoadMore, itemCount: 20 });

        await flushFrames();
        // Both signals land while the same page is still displayed, as they do in a real browser frame.
        fireIntersection(true);
        await fireResize();

        expect(onLoadMore).toHaveBeenCalledTimes(1);
    });

    it('observes the list against the viewport so any scrolling element triggers a load', () => {
        renderOffScreen({ onLoadMore: vi.fn() });

        const options = (globalThis.IntersectionObserver as any).mock.calls[0][1];
        expect(options.root).toBeUndefined();
    });

    it('observes a stable marker below the rows, never a row that gets replaced', () => {
        const { getByTestId, rerender } = render(<Harness itemCount={1} />);
        const sentinel = getByTestId('sentinel');

        rerender(<Harness itemCount={21} />);

        const observer = (globalThis.IntersectionObserver as any).mock.results[0].value;
        const targets = observer.observe.mock.calls.map((call: any[]) => call[0]);
        expect(targets).toEqual([sentinel]);
        expect(targets.every(target => target.tagName !== 'TR')).toBe(true);
    });

    it('keeps reacting to the sentinel after a page is appended', () => {
        const onLoadMore = vi.fn();
        const { rerender } = renderOffScreen({ onLoadMore, itemCount: 20 });

        fireIntersection(true);
        expect(onLoadMore).toHaveBeenCalledTimes(1);

        rerender(<Harness onLoadMore={onLoadMore} itemCount={40} />);
        fireIntersection(true);
        expect(onLoadMore).toHaveBeenCalledTimes(2);
    });
});
