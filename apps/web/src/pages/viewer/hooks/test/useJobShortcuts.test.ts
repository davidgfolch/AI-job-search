import { renderHook, act, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useJobShortcuts } from '../useJobShortcuts';
import { UI_SHORTCUTS_STORAGE_KEY } from '../../shortcutsConfig';

const mockUseEnvSettings = vi.fn();
vi.mock('../../../common/hooks/useEnvSettings', () => ({
    useEnvSettings: (...args: unknown[]) => mockUseEnvSettings(...args),
}));

const onAction = vi.fn();
const onPinnedConfigShortcut = vi.fn();

const render = () => renderHook(() => useJobShortcuts({ onAction, onPinnedConfigShortcut }));

describe('useJobShortcuts', () => {
    beforeEach(() => {
        localStorage.clear();
        onAction.mockClear();
        onPinnedConfigShortcut.mockClear();
        mockUseEnvSettings.mockReturnValue({ data: undefined });
    });

    it('fires action for matching alt combo', () => {
        render();
        fireEvent.keyDown(window, { key: 'i', altKey: true });
        expect(onAction).toHaveBeenCalledWith('ignore');
    });

    it('uses env-defined ctrl combos', () => {
        mockUseEnvSettings.mockReturnValue({ data: { UI_SHORTCUTS_IGNORE: 'ctrl+i' } });
        render();
        fireEvent.keyDown(window, { key: 'i', ctrlKey: true });
        expect(onAction).toHaveBeenCalledWith('ignore');
        fireEvent.keyDown(window, { key: 'i', altKey: true });
        expect(onAction).toHaveBeenCalledTimes(1);
    });

    it('does not fire when disabled', () => {
        const { result } = render();
        act(() => result.current.toggleEnabled());
        fireEvent.keyDown(window, { key: 'i', altKey: true });
        expect(onAction).not.toHaveBeenCalled();
    });

    it('ignores editable targets', () => {
        render();
        const input = document.createElement('input');
        document.body.appendChild(input);
        try {
            fireEvent.keyDown(input, { key: 'i', altKey: true });
            expect(onAction).not.toHaveBeenCalled();
        } finally {
            document.body.removeChild(input);
        }
    });

    it('ignores keys when a modal is open', () => {
        render();
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        document.body.appendChild(overlay);
        try {
            fireEvent.keyDown(window, { key: 'i', altKey: true });
            expect(onAction).not.toHaveBeenCalled();
        } finally {
            document.body.removeChild(overlay);
        }
    });

    it('does not fire for non-matching keys', () => {
        render();
        fireEvent.keyDown(window, { key: 'x', altKey: true });
        fireEvent.keyDown(window, { key: 'i' });
        expect(onAction).not.toHaveBeenCalled();
    });

    it('persists the toggle in localStorage', () => {
        const { result } = render();
        act(() => result.current.toggleEnabled());
        expect(localStorage.getItem(UI_SHORTCUTS_STORAGE_KEY)).toBe('false');
        act(() => result.current.toggleEnabled());
        expect(localStorage.getItem(UI_SHORTCUTS_STORAGE_KEY)).toBe('true');
    });

    it('initializes disabled from localStorage', () => {
        localStorage.setItem(UI_SHORTCUTS_STORAGE_KEY, 'false');
        const { result } = render();
        expect(result.current.enabled).toBe(false);
        fireEvent.keyDown(window, { key: 'i', altKey: true });
        expect(onAction).not.toHaveBeenCalled();
    });

    it('fires pinned config shortcut for alt+digit by position', () => {
        render();
        fireEvent.keyDown(window, { key: '3', altKey: true });
        expect(onPinnedConfigShortcut).toHaveBeenCalledWith(3);
    });

    it('does not fire pinned config shortcut without alt', () => {
        render();
        fireEvent.keyDown(window, { key: '2' });
        expect(onPinnedConfigShortcut).not.toHaveBeenCalled();
    });

    it('does not fire pinned config shortcut for non-digit keys', () => {
        render();
        fireEvent.keyDown(window, { key: 'a', altKey: true });
        expect(onPinnedConfigShortcut).not.toHaveBeenCalled();
    });

    it('does not fire pinned config shortcut with ctrl', () => {
        render();
        fireEvent.keyDown(window, { key: '1', altKey: true, ctrlKey: true });
        expect(onPinnedConfigShortcut).not.toHaveBeenCalled();
    });

    it('does not fire when disabled', () => {
        const { result } = render();
        act(() => result.current.toggleEnabled());
        fireEvent.keyDown(window, { key: '1', altKey: true });
        expect(onPinnedConfigShortcut).not.toHaveBeenCalled();
    });

    it('respects env UI_SHORTCUTS_ENABLED default when nothing stored', () => {
        mockUseEnvSettings.mockReturnValue({ data: { UI_SHORTCUTS_ENABLED: 'false' } });
        const { result } = render();
        expect(result.current.enabled).toBe(false);
        fireEvent.keyDown(window, { key: 'i', altKey: true });
        expect(onAction).not.toHaveBeenCalled();
    });

    it('returns resolved shortcuts from env settings', () => {
        mockUseEnvSettings.mockReturnValue({ data: { UI_SHORTCUTS_APPLY: 'ctrl+a' } });
        const { result } = render();
        expect(result.current.shortcuts.apply).toEqual({ ctrl: true, alt: false, key: 'a', display: 'Ctrl+A' });
        expect(result.current.shortcuts.ignore.display).toBe('Alt+I');
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

    it('resets modifierPressed on window focus', () => {
        const { result } = render();
        fireEvent.keyDown(window, { key: 'Alt' });
        expect(result.current.modifierPressed).toBe(true);
        fireEvent.focus(window);
        expect(result.current.modifierPressed).toBe(false);
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
