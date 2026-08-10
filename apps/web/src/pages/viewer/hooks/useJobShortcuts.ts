import { useCallback, useEffect, useState } from 'react';
import { useEnvSettings } from '../../common/hooks/useEnvSettings';
import { resolveShortcuts, SHORTCUT_ACTIONS, type ShortcutAction } from '../shortcutsConfig';
import { UI_SHORTCUTS_ENABLED_KEY, UI_SHORTCUTS_STORAGE_KEY } from '../shortcutsConfig';

const isEditableTarget = (target: EventTarget | null): boolean => {
    if (!(target instanceof HTMLElement)) return false;
    return target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT' || target.isContentEditable;
};

interface UseJobShortcutsProps {
    onAction: (action: ShortcutAction) => void;
}

export const useJobShortcuts = ({ onAction }: UseJobShortcutsProps) => {
    const { data: envSettings } = useEnvSettings();
    const shortcuts = resolveShortcuts(envSettings);
    const [storedEnabled, setStoredEnabled] = useState<boolean | null>(() => {
        const stored = localStorage.getItem(UI_SHORTCUTS_STORAGE_KEY);
        return stored === null ? null : stored === 'true';
    });
    const enabled = storedEnabled ?? (envSettings ? envSettings[UI_SHORTCUTS_ENABLED_KEY] !== 'false' : true);

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
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [enabled, shortcuts, onAction]);

    return { enabled, toggleEnabled, shortcuts };
};
