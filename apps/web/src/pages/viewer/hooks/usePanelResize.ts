import { useCallback, useEffect, useRef, useState, type CSSProperties, type KeyboardEvent as ReactKeyboardEvent, type PointerEvent as ReactPointerEvent } from 'react';

export const DEFAULT_LIST_RATIO = 0.5;
export const MIN_LIST_RATIO = 0.2;
export const MAX_LIST_RATIO = 0.8;
export const PANEL_RATIO_STORAGE_KEY = 'viewer-list-ratio';
const KEYBOARD_STEP = 0.02;

const clampRatio = (value: number) => Math.min(MAX_LIST_RATIO, Math.max(MIN_LIST_RATIO, value));

const readStoredRatio = (): number => {
    try {
        const stored = localStorage.getItem(PANEL_RATIO_STORAGE_KEY);
        const parsed = stored === null ? NaN : Number(stored);
        return Number.isFinite(parsed) ? clampRatio(parsed) : DEFAULT_LIST_RATIO;
    } catch {
        return DEFAULT_LIST_RATIO;
    }
};

export interface ResizeHandleProps {
    onPointerDown: (event: ReactPointerEvent<HTMLDivElement>) => void;
    onPointerMove: (event: ReactPointerEvent<HTMLDivElement>) => void;
    onPointerUp: (event: ReactPointerEvent<HTMLDivElement>) => void;
    onPointerCancel: (event: ReactPointerEvent<HTMLDivElement>) => void;
    onKeyDown: (event: ReactKeyboardEvent<HTMLDivElement>) => void;
}

export function usePanelResize(duplicated: boolean) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [collapsedPanel, setCollapsedPanel] = useState<'none' | 'left' | 'right'>('none');
    const [listRatio, setListRatio] = useState(readStoredRatio);
    const [isDragging, setIsDragging] = useState(false);
    const dragRef = useRef<{ startX: number; startRatio: number; width: number } | null>(null);
    const leftHidden = duplicated || collapsedPanel === 'left';
    const resizeEnabled = !leftHidden && collapsedPanel === 'none';

    useEffect(() => {
        try {
            localStorage.setItem(PANEL_RATIO_STORAGE_KEY, String(listRatio));
        } catch {
            // Storage can be disabled; the split still works for this session.
        }
    }, [listRatio]);

    const onPointerDown = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
        const width = containerRef.current?.getBoundingClientRect().width ?? 0;
        if (!resizeEnabled || event.button !== 0 || width <= 0) return;
        dragRef.current = { startX: event.clientX, startRatio: listRatio, width };
        event.currentTarget.setPointerCapture(event.pointerId);
        setIsDragging(true);
        event.preventDefault();
    }, [resizeEnabled, listRatio]);

    const onPointerMove = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
        const drag = dragRef.current;
        if (!drag) return;
        setListRatio(clampRatio(drag.startRatio + (event.clientX - drag.startX) / drag.width));
    }, []);

    const endDrag = useCallback((event: ReactPointerEvent<HTMLDivElement>) => {
        if (!dragRef.current) return;
        dragRef.current = null;
        setIsDragging(false);
        if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    }, []);

    const resizeBy = useCallback((delta: number) => setListRatio(prev => clampRatio(prev + delta)), []);

    const onKeyDown = useCallback((event: ReactKeyboardEvent<HTMLDivElement>) => {
        if (!resizeEnabled) return;
        if (event.key === 'ArrowLeft') resizeBy(-KEYBOARD_STEP);
        else if (event.key === 'ArrowRight') resizeBy(KEYBOARD_STEP);
        else if (event.key === 'Home') setListRatio(DEFAULT_LIST_RATIO);
        else return;
        event.preventDefault();
    }, [resizeEnabled, resizeBy]);

    const handleProps: ResizeHandleProps = { onPointerDown, onPointerMove, onPointerUp: endDrag, onPointerCancel: endDrag, onKeyDown };
    const toggleCollapse = useCallback((panel: 'left' | 'right') => setCollapsedPanel(prev => prev === panel ? 'none' : panel), []);
    const resetPanels = useCallback(() => { setCollapsedPanel('none'); setListRatio(DEFAULT_LIST_RATIO); }, []);
    const contentProps = { ref: containerRef, style: { '--list-ratio': leftHidden ? 0 : collapsedPanel === 'right' ? 1 : listRatio } as CSSProperties };
    const dividerProps = { collapsedPanel, onCollapse: toggleCollapse, listRatio, resizeHandleProps: handleProps, isDragging, resizeEnabled };
    return { collapsedPanel, leftHidden, contentProps, dividerProps, resetPanels };
}
