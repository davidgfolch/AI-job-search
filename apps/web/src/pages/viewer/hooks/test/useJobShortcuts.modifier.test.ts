import { renderHook, act, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useJobShortcuts } from '../useJobShortcuts';

const mockUseEnvSettings = vi.fn();
vi.mock('../../../common/hooks/useEnvSettings', () => ({
    useEnvSettings: (...args: unknown[]) => mockUseEnvSettings(...args),
}));

const onAction = vi.fn();
const onPinnedConfigShortcut = vi.fn();

const render = () => renderHook(() => useJobShortcuts({ onAction, onPinnedConfigShortcut }));

describe('useJobShortcuts modifierPressed', () => {
    beforeEach(() => {
        localStorage.clear();
        onAction.mockClear();
        onPinnedConfigShortcut.mockClear();
        mockUseEnvSettings.mockReturnValue({ data: undefined });
    });

    it('tracks modifierPressed while alt is held', () => {
        const { result } = render();
        expect(result.current.modifierPressed).toBe(false);
        fireEvent.keyDown(window, { key: 'Alt' });
        expect(result.current.modifierPressed).toBe(true);
        fireEvent.keyUp(window, { key: 'Alt' });
        expect(result.current.modifierPressed).toBe(false);
    });

    it('tracks modifierPressed while ctrl is held when shortcuts use ctrl', () => {
        mockUseEnvSettings.mockReturnValue({ data: { UI_SHORTCUTS_IGNORE: 'ctrl+i' } });
        const { result } = render();
        fireEvent.keyDown(window, { key: 'Control' });
        expect(result.current.modifierPressed).toBe(true);
        fireEvent.keyUp(window, { key: 'Control' });
        expect(result.current.modifierPressed).toBe(false);
    });

    it('does not track ctrl when all shortcuts use alt', () => {
        const { result } = render();
        fireEvent.keyDown(window, { key: 'Control' });
        expect(result.current.modifierPressed).toBe(false);
    });

    it('keeps modifierPressed while alt is held even when the window regains focus', () => {
        const { result } = render();
        fireEvent.keyDown(window, { key: 'Alt' });
        expect(result.current.modifierPressed).toBe(true);
        fireEvent.focus(window);
        expect(result.current.modifierPressed).toBe(true);
    });

    it('picks up modifierPressed from mouse events when the key event was consumed', () => {
        const { result } = render();
        fireEvent.mouseMove(window, { altKey: true });
        expect(result.current.modifierPressed).toBe(true);
        fireEvent.mouseMove(window, { altKey: false });
        expect(result.current.modifierPressed).toBe(true);
    });

    it('tracks modifierPressed via altKey state regardless of key name', () => {
        const { result } = render();
        fireEvent.keyDown(window, { key: 'AltGraph', altKey: true });
        expect(result.current.modifierPressed).toBe(true);
        fireEvent.keyUp(window, { key: 'AltGraph' });
        expect(result.current.modifierPressed).toBe(false);
    });

    it('does not track modifier when shortcuts disabled', () => {
        const { result } = render();
        act(() => result.current.toggleEnabled());
        fireEvent.keyDown(window, { key: 'Alt' });
        expect(result.current.modifierPressed).toBe(false);
    });
});
