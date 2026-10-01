import { useCallback, useEffect, useRef } from 'react';

const FILL_TOLERANCE_PX = 2;
const TRIGGER_MARGIN_PX = 200;

interface UseAutoLoadMoreOptions {
    contentRef: React.RefObject<HTMLElement | null>;
    sentinelRef: React.RefObject<HTMLElement | null>;
    itemCount: number;
    hasMore?: boolean;
    isLoading?: boolean;
    onLoadMore?: () => void;
}

/** Requests the next page of a scrollable list.
 *
 * Triggers from two viewport-relative signals, so it works no matter which element actually scrolls and
 * regardless of font size or screen height:
 *  - the end of the list is already on screen (nothing left to scroll to), and
 *  - the end of the list is scrolled into view.
 * The sentinel must be a stable node: observing the last row breaks as soon as a page is appended, because
 * that row stops being the last one. */
export const useAutoLoadMore = ({ contentRef, sentinelRef, itemCount, hasMore, isLoading, onLoadMore }: UseAutoLoadMoreOptions) => {
    const stateRef = useRef({ onLoadMore, hasMore: !!hasMore, isLoading: !!isLoading, itemCount });
    useEffect(() => { stateRef.current = { onLoadMore, hasMore: !!hasMore, isLoading: !!isLoading, itemCount }; });

    /** Whether the end of the list sits within `margin` pixels of the bottom of the viewport. */
    const isEndOfListWithin = useCallback((margin: number) => {
        const sentinel = sentinelRef.current;
        if (!sentinel) return false;
        const rect = sentinel.getBoundingClientRect();
        // A zero-sized rect means the list is hidden (inactive tab) or not laid out yet.
        if (rect.height === 0 && rect.width === 0) return false;
        return rect.bottom <= window.innerHeight + margin;
    }, [sentinelRef]);

    const isEndOfListOnScreen = useCallback(() => isEndOfListWithin(FILL_TOLERANCE_PX), [isEndOfListWithin]);

    // Latched synchronously: the fill frame and the intersection callback can both land in the same frame,
    // before `isLoading` has had a chance to propagate back into the ref. Re-armed once the page has landed
    // or the request has settled, so one request is ever in flight.
    const inFlightRef = useRef(false);
    useEffect(() => { inFlightRef.current = false; }, [itemCount]);
    useEffect(() => { if (!isLoading) inFlightRef.current = false; }, [isLoading]);

    const requestLoadMore = useCallback(() => {
        const { onLoadMore: loadMore, hasMore: more, isLoading: busy, itemCount: items } = stateRef.current;
        // An empty list is trivially "on screen", so its geometry says nothing about whether more is needed.
        if (!loadMore || !more || busy || inFlightRef.current || items === 0) return;
        inFlightRef.current = true;
        loadMore();
    }, []);

    // The end of the list is already visible, so there is nothing to scroll: fetch the next page. Every
    // appended page changes itemCount, re-running this until the list overflows the screen or runs out.
    useEffect(() => {
        if (!hasMore || isLoading) return;
        const frame = requestAnimationFrame(() => { if (isEndOfListOnScreen()) requestLoadMore(); });
        return () => cancelAnimationFrame(frame);
    }, [hasMore, isLoading, itemCount, isEndOfListOnScreen, requestLoadMore]);

    // Re-check after the content resizes: a taller window, a wider column or a bigger font can leave the
    // end of the list on screen again.
    useEffect(() => {
        const content = contentRef.current;
        if (!content || typeof ResizeObserver === 'undefined') return;
        let frame = 0;
        const observer = new ResizeObserver(() => {
            cancelAnimationFrame(frame);
            frame = requestAnimationFrame(() => { if (isEndOfListOnScreen()) requestLoadMore(); });
        });
        observer.observe(content);
        return () => { cancelAnimationFrame(frame); observer.disconnect(); };
    }, [contentRef, isEndOfListOnScreen, requestLoadMore]);

    // The end of the list is scrolled into view. Rooted at the viewport so it does not matter whether the
    // list container, an ancestor or the window is the element that scrolls.
    useEffect(() => {
        const sentinel = sentinelRef.current;
        if (!sentinel || typeof IntersectionObserver === 'undefined') return;
        const observer = new IntersectionObserver((entries) => {
            if (entries.some(entry => entry.isIntersecting)) requestLoadMore();
        }, { rootMargin: `${TRIGGER_MARGIN_PX}px` });
        observer.observe(sentinel);
        return () => observer.disconnect();
    }, [sentinelRef, requestLoadMore]);

    // Fallback for the scroll signal: Firefox does not report intersection changes caused by a nested
    // container scroll, and the observer alone is not enough. Listening in the capture phase also covers
    // the scroll of any ancestor, so this fires whoever actually scrolls.
    useEffect(() => {
        if (!hasMore) return;
        let frame = 0;
        const handleScroll = () => {
            cancelAnimationFrame(frame);
            frame = requestAnimationFrame(() => { if (isEndOfListWithin(TRIGGER_MARGIN_PX)) requestLoadMore(); });
        };
        window.addEventListener('scroll', handleScroll, { capture: true, passive: true });
        return () => { cancelAnimationFrame(frame); window.removeEventListener('scroll', handleScroll, { capture: true }); };
    }, [hasMore, isEndOfListWithin, requestLoadMore]);

    return { isEndOfListOnScreen, requestLoadMore };
};
