import { createContext, useContext } from 'react';
import { DEFAULT_SHORTCUTS, parseShortcut, type ShortcutAction, type ShortcutCombo } from './shortcutsConfig';

export interface ShortcutsContextValue {
    shortcuts: Record<ShortcutAction, ShortcutCombo>;
    modifierPressed: boolean;
}

export const defaultValue = (): ShortcutsContextValue => ({
    shortcuts: Object.fromEntries(
        (Object.entries(DEFAULT_SHORTCUTS) as [ShortcutAction, string][]).map(([action, combo]) => [action, parseShortcut(combo)]),
    ) as Record<ShortcutAction, ShortcutCombo>,
    modifierPressed: false,
});

export const ShortcutsContext = createContext<ShortcutsContextValue>(defaultValue());

export const useShortcuts = (): ShortcutsContextValue => useContext(ShortcutsContext);