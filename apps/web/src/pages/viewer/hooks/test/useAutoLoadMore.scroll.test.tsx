import { render } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
    Harness, installObserverMocks, setWindowHeight, flushFrames, fireIntersection, fireResize,
    fireScroll, setSentinelBottom, renderOnScreen, renderOffScreen,
    ON_SCREEN_BOTTOM, VIEWPORT_HEIGHT,
} from './useAutoLoadMore.fixtures';

describe('useAutoLoadMore scroll and observer signals', () => {
    beforeEach(() => {
        installObserverMocks();
        setWindowHeight(VIEWPORT_HEIGHT);
    });

    afterEach(() => {
        vi.restoreAllMocks();
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
