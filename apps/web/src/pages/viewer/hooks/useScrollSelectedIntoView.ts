import { useLayoutEffect } from 'react';

interface UseScrollSelectedIntoViewOptions {
    containerRef: React.RefObject<HTMLElement | null>;
    rowRef: React.RefObject<HTMLElement | null>;
    selectedId?: number;
}

/** Height of the sticky header the rows slide under. It floats over the list, so the top of the scroll port
 * is not readable and a row parked there is indistinguishable from one that was never scrolled to. */
const stickyHeaderHeight = (row: HTMLElement) => row.closest('table')?.tHead?.getBoundingClientRect().height ?? 0;

/** Keeps the selected row inside the visible frame of the jobs list.
 *
 * `scrollIntoView` is not enough here: it aligns the row with the nearest edge of the scroll port, which for
 * an upward step is the edge the sticky header covers, so the job still reads as missing. Scrolling the
 * container itself by the smallest amount that clears both the header and the bottom edge keeps the list and
 * the selection in sync in both directions, and is a no-op while the row is already readable. */
export const useScrollSelectedIntoView = ({ containerRef, rowRef, selectedId }: UseScrollSelectedIntoViewOptions) => {
    useLayoutEffect(() => {
        const container = containerRef.current;
        const row = rowRef.current;
        if (selectedId === undefined || !container || !row) return;
        const containerRect = container.getBoundingClientRect();
        const rowRect = row.getBoundingClientRect();
        // No layout yet, which is what a hidden tab or a collapsed panel reports: there is no frame to fit into.
        if (!containerRect.height || !rowRect.height) return;
        const frameTop = containerRect.top + stickyHeaderHeight(row);
        // A row taller than the frame can never fit in it, so anchor it right below the header instead.
        const anchorAtTop = rowRect.top < frameTop || rowRect.height > containerRect.bottom - frameTop;
        const deltaTop = anchorAtTop ? rowRect.top - frameTop
            : rowRect.bottom > containerRect.bottom ? rowRect.bottom - containerRect.bottom : 0;
        const deltaLeft = rowRect.left < containerRect.left ? rowRect.left - containerRect.left
            : rowRect.right > containerRect.right ? rowRect.right - containerRect.right : 0;
        if (deltaTop !== 0) container.scrollTop += deltaTop;
        if (deltaLeft !== 0) container.scrollLeft += deltaLeft;
    }, [selectedId, containerRef, rowRef]);
};
