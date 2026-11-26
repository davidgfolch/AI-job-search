import { useEffect, useRef } from 'react';

/**
 * Automatically resizes a textarea based on its content scrollHeight.
 * Uses ResizeObserver to detect when the element's size changes due to content wrapping,
 * avoiding layout thrashing on every keystroke.
 * @param ref - Reference to the textarea element
 * @param dependencies - Additional dependencies that should trigger a resize (e.g., visibility changes)
 */
export function useAutoResizeTextArea(
    ref: React.RefObject<HTMLTextAreaElement | null>,
    dependencies: unknown[] = []
) {
    // Use a ref to store the resize function so it's stable across renders
    const resizeRef = useRef<() => void>();

    useEffect(() => {
        const element = ref.current;
        if (!element) return;

        const resize = () => {
            element.style.height = 'auto';
            element.style.height = `${element.scrollHeight + 5}px`;
        };

        // Store resize function in ref for ResizeObserver callback
        resizeRef.current = resize;

        // Initial resize
        resize();

        // Use ResizeObserver to detect content size changes
        // This fires when the textarea's content size changes (e.g., text wraps to new line)
        const observer = new ResizeObserver(() => {
            resizeRef.current?.();
        });
        observer.observe(element);

        // Also handle window resize
        window.addEventListener('resize', resize);

        // IntersectionObserver to detect when the element becomes visible
        // This solves issues where the component is mounted but hidden (e.g. inside a modal/tab)
        // and scrollHeight is 0 until it becomes visible.
        const intersectionObserver = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    resize();
                }
            });
        });
        intersectionObserver.observe(element);

        return () => {
            observer.disconnect();
            intersectionObserver.disconnect();
            window.removeEventListener('resize', resize);
        };
    }, [ref, ...dependencies]);
}