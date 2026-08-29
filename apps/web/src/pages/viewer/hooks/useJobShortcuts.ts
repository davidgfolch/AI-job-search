import { useCallback, useEffect, useState } from 'react';
import { useEnvSettings } from '../../common/hooks/useEnvSettings';
import { resolveShortcuts, SHORTCUT_ACTIONS, type ShortcutAction } from '../shortcutsConfig';
import { UI_SHORTCUTS_ENABLED_KEY, UI_SHORTCUTS_STORAGE_KEY } from '../shortcutsConfig';

const isEditableTarget = (target: EventTarget | null): boolean => {
    if (!(target instanceof HTMLElement)) return false;
    if (target.tagName === 'INPUT') {
        const type = (target as HTMLInputElement).type.toLowerCase();
        return !['checkbox', 'radio', 'button', 'submit', 'reset', 'range', 'color'].includes(type);
    }
    return target.tagName === 'TEXTAREA' || target.tagName === 'SELECT' || target.isContentEditable;
};

interface UseJobShortcutsProps {
    onAction: (action: ShortcutAction) => void;
    onPinnedConfigShortcut?: (index: number) => void;
}

export const useJobShortcuts = ({ onAction, onPinnedConfigShortcut }: UseJobShortcutsProps) => {
    const { data: envSettings } = useEnvSettings();
    const shortcuts = resolveShortcuts(envSettings);
    const [storedEnabled, setStoredEnabled] = useState<boolean | null>(() => {
        const stored = localStorage.getItem(UI_SHORTCUTS_STORAGE_KEY);
        return stored === null ? null : stored === 'true';
    });
    const enabled = storedEnabled ?? (envSettings ? envSettings[UI_SHORTCUTS_ENABLED_KEY] !== 'false' : true);
    const [modifierPressed, setModifierPressed] = useState(false);

    const toggleEnabled = useCallback(() => {
        setStoredEnabled(prev => {
            const next = !(prev !== null ? prev : enabled);
            localStorage.setItem(UI_SHORTCUTS_STORAGE_KEY, String(next));
            return next;
        });
    }, [enabled]);

    useEffect(() => {
        if (!enabled) return;
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.altKey) return;
            if (isEditableTarget(e.target)) return;
            if (document.querySelector('.modal-overlay')) return;
            const key = e.key.toLowerCase();
            for (const info of SHORTCUT_ACTIONS) {
                const combo = shortcuts[info.action];
                if (e.ctrlKey === combo.ctrl && e.altKey === combo.alt && key === combo.key) {
                    e.preventDefault();
                    onAction(info.action);
                    return;
                }
            }
            if (!e.ctrlKey && e.altKey && key >= '1' && key <= '9' && onPinnedConfigShortcut) {
                e.preventDefault();
                onPinnedConfigShortcut(Number(key));
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [enabled, shortcuts, onAction, onPinnedConfigShortcut]);

    useEffect(() => {
        const trackedModifiers = new Set<string>(['alt']);
        for (const info of SHORTCUT_ACTIONS) {
            trackedModifiers.add(shortcuts[info.action].ctrl ? 'ctrl' : 'alt');
        }
        const trackAlt = trackedModifiers.has('alt');
        const trackCtrl = trackedModifiers.has('ctrl');
        const isAltKey = (e: KeyboardEvent): boolean => {
            const k = e.key.toLowerCase();
            return k === 'alt' || k === 'altgraph';
        };
        const isCtrlKey = (e: KeyboardEvent): boolean => e.key.toLowerCase() === 'control';
        const onKeyDown = (e: KeyboardEvent) => {
            if (!enabled) return;
            if (trackAlt && (isAltKey(e) || e.altKey)) setModifierPressed(true);
            if (trackCtrl && (isCtrlKey(e) || e.ctrlKey)) setModifierPressed(true);
        };
        const onKeyUp = (e: KeyboardEvent) => {
            if (trackAlt && (isAltKey(e) || !e.altKey)) setModifierPressed(false);
            if (trackCtrl && (isCtrlKey(e) || !e.ctrlKey)) setModifierPressed(false);
        };
        const onFocus = () => setModifierPressed(false);
        window.addEventListener('keydown', onKeyDown);
        window.addEventListener('keyup', onKeyUp);
        window.addEventListener('focus', onFocus);
        return () => {
            window.removeEventListener('keydown', onKeyDown);
            window.removeEventListener('keyup', onKeyUp);
            window.removeEventListener('focus', onFocus);
        };
    }, [enabled, shortcuts]);

    return { enabled, toggleEnabled, shortcuts, modifierPressed };
};
