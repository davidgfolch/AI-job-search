import { fireEvent, render, screen } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PANEL_RATIO_STORAGE_KEY, usePanelResize } from '../usePanelResize';
import { stubElementRect } from '../../test/test-utils';

function Harness({ duplicated = false }: { duplicated?: boolean }) {
    const { contentProps, dividerProps, resetPanels } = usePanelResize(duplicated);
    return (
        <div {...contentProps} data-testid="container">
            <div data-testid="handle" {...dividerProps.resizeHandleProps}>{dividerProps.listRatio}</div>
            <button data-testid="collapse" onClick={() => dividerProps.onCollapse('left')} />
            <button data-testid="collapse-detail" onClick={() => dividerProps.onCollapse('right')} />
            <span data-testid="collapsed">{dividerProps.collapsedPanel}</span>
            <button data-testid="reset" onClick={resetPanels} />
        </div>
    );
}

const setupHandle = () => {
    const handle = screen.getByTestId('handle');
    handle.setPointerCapture = vi.fn();
    handle.hasPointerCapture = vi.fn(() => true);
    handle.releasePointerCapture = vi.fn();
    stubElementRect(screen.getByTestId('container'), { left: 0, right: 1000 });
    return handle;
};

const ratio = () => Number(screen.getByTestId('handle').textContent);

describe('usePanelResize', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    it('starts at 50/50 and persists it', () => {
        render(<Harness />);
        expect(ratio()).toBe(0.5);
        expect(localStorage.getItem(PANEL_RATIO_STORAGE_KEY)).toBe('0.5');
    });

    it('restores a saved ratio and clamps invalid values into the allowed range', () => {
        const values = [['0.7', 0.7], ['5', 0.8], ['-3', 0.2], ['not-a-number', 0.5]] as const;
        values.forEach(([stored, expected]) => {
            localStorage.setItem(PANEL_RATIO_STORAGE_KEY, stored);
            const view = render(<Harness />);
            expect(ratio()).toBe(expected);
            view.unmount();
        });
    });

    it('resizes by the drag delta relative to the container width, clamped', () => {
        render(<Harness />);
        const handle = setupHandle();
        fireEvent.pointerDown(handle, { clientX: 200, button: 0, pointerId: 1 });
        fireEvent.pointerMove(handle, { clientX: 400, pointerId: 1 });
        expect(ratio()).toBe(0.7);
        fireEvent.pointerMove(handle, { clientX: -5000, pointerId: 1 });
        expect(ratio()).toBe(0.2);
        fireEvent.pointerUp(handle, { pointerId: 1 });
        expect(handle.releasePointerCapture).toHaveBeenCalled();
    });

    it('supports keyboard resizing and Home resets to 50/50', () => {
        localStorage.setItem(PANEL_RATIO_STORAGE_KEY, '0.7');
        render(<Harness />);
        const handle = screen.getByTestId('handle');
        fireEvent.keyDown(handle, { key: 'ArrowRight' });
        expect(ratio()).toBe(0.72);
        fireEvent.keyDown(handle, { key: 'ArrowLeft' });
        expect(ratio()).toBe(0.7);
        fireEvent.keyDown(handle, { key: 'Home' });
        expect(ratio()).toBe(0.5);
    });

    it('ignores drag and keyboard input when a panel is hidden', () => {
        render(<Harness />);
        fireEvent.click(screen.getByTestId('collapse'));
        const handle = setupHandle();
        fireEvent.pointerDown(handle, { clientX: 200, button: 0, pointerId: 1 });
        fireEvent.pointerMove(handle, { clientX: 600, pointerId: 1 });
        fireEvent.keyDown(handle, { key: 'ArrowRight' });
        expect(ratio()).toBe(0.5);
    });

    it('toggles a collapsed panel back with the same button', () => {
        render(<Harness />);
        fireEvent.click(screen.getByTestId('collapse'));
        expect(screen.getByTestId('collapsed').textContent).toBe('left');
        fireEvent.click(screen.getByTestId('collapse'));
        expect(screen.getByTestId('collapsed').textContent).toBe('none');
    });

    it('gives the list all the split space when the detail is collapsed', () => {
        render(<Harness />);
        const container = screen.getByTestId('container') as HTMLElement;
        fireEvent.click(screen.getByTestId('collapse-detail'));
        expect(container.style.getPropertyValue('--list-ratio')).toBe('1');
        fireEvent.click(screen.getByTestId('collapse-detail'));
        expect(container.style.getPropertyValue('--list-ratio')).toBe('0.5');
    });

    it('disables resizing for a duplicated job and restores both panels on reset', () => {
        const { rerender } = render(<Harness duplicated />);
        const handle = setupHandle();
        fireEvent.pointerDown(handle, { clientX: 200, button: 0, pointerId: 1 });
        fireEvent.pointerMove(handle, { clientX: 600, pointerId: 1 });
        expect(ratio()).toBe(0.5);
        rerender(<Harness />);
        fireEvent.pointerDown(handle, { clientX: 200, button: 0, pointerId: 1 });
        fireEvent.pointerMove(handle, { clientX: 600, pointerId: 1 });
        expect(ratio()).toBe(0.8);
        fireEvent.click(screen.getByTestId('collapse'));
        expect(screen.getByTestId('collapsed').textContent).toBe('left');
        fireEvent.click(screen.getByTestId('reset'));
        expect(ratio()).toBe(0.5);
        expect(screen.getByTestId('collapsed').textContent).toBe('none');
    });
});
