
import { useLayoutEffect } from 'react';

/**
 * Automatically resizes a textarea based on its content scrollHeight.
 * @param ref - Reference to the textarea element
 * @param value - The current value of the textarea
 * @param dependencies - Additional dependencies that should trigger a resize (e.g., visibility changes)
 */
export function useAutoResizeTextArea(
    ref: React.RefObject<HTMLTextAreaElement | null>,
    value: string,
    dependencies: any[] = []
) {
    useLayoutEffect(() => {
        const element = ref.current;
        if (!element) return;

        const resize = () => {
            element.style.height = 'auto';
            element.style.height = `${element.scrollHeight+5}px`;
        };

        // Initial resize
        resize();

        // Safety resize for layout shifts (e.g. CSS transitions)
        const rAF = requestAnimationFrame(() => {
            resize();
            // Double rAF to ensure we are in the next frame after any reflows
            requestAnimationFrame(resize);
        });
        
        // Fallback timeout for slower layout updates
        const timer = setTimeout(resize, 100);

        window.addEventListener('resize', resize);
        
        // Use IntersectionObserver to detect when the element becomes visible
        // This solves issues where the component is mounted but hidden (e.g. inside a modal/tab)
        // and scrollHeight is 0 until it becomes visible.
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    resize();
                }
            });
        });
        observer.observe(element);

        return () => {
            cancelAnimationFrame(rAF);
            clearTimeout(timer);
            window.removeEventListener('resize', resize);
            observer.disconnect();
        };
    }, [value, ref, ...dependencies]);
}
