import { render } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
    Harness, hideSentinel, installObserverMocks, setWindowHeight, flushFrames, fireIntersection,
    fireResize, setSentinelBottom, renderOnScreen, renderOffScreen,
    ON_SCREEN_BOTTOM, OFF_SCREEN_BOTTOM, VIEWPORT_HEIGHT,
} from './useAutoLoadMore.fixtures';

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
});
