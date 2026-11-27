import { describe, it, expect } from 'vitest';
import { parseShortcut, pinnedShortcutDisplay, pinnedShortcutPosition, resolveShortcuts, DEFAULT_SHORTCUTS, SHORTCUT_ACTIONS, SHORTCUT_ENV_KEYS } from '../shortcutsConfig';

describe('parseShortcut', () => {
    it('parses lowercase alt combo', () => {
        expect(parseShortcut('alt+i')).toEqual({ ctrl: false, alt: true, key: 'i', display: 'Alt+I' });
    });

    it('parses uppercase ctrl combo case-insensitively', () => {
        expect(parseShortcut('CTRL+A')).toEqual({ ctrl: true, alt: false, key: 'a', display: 'Ctrl+A' });
    });

    it('returns null for invalid values', () => {
        expect(parseShortcut(undefined)).toBeNull();
        expect(parseShortcut('')).toBeNull();
        expect(parseShortcut('shift+i')).toBeNull();
        expect(parseShortcut('alt+')).toBeNull();
        expect(parseShortcut('alt+ii')).toBeNull();
        expect(parseShortcut('alt+shift+i')).toBeNull();
    });
});

describe('resolveShortcuts', () => {
    it('uses defaults when env settings are missing', () => {
        const resolved = resolveShortcuts(undefined);
        for (const info of SHORTCUT_ACTIONS) {
            expect(resolved[info.action]).toEqual(parseShortcut(DEFAULT_SHORTCUTS[info.action]));
        }
    });

    it('overrides defaults from env settings', () => {
        const resolved = resolveShortcuts({ UI_SHORTCUTS_IGNORE: 'ctrl+i' });
        expect(resolved.ignore).toEqual({ ctrl: true, alt: false, key: 'i', display: 'Ctrl+I' });
        expect(resolved.apply).toEqual(parseShortcut(DEFAULT_SHORTCUTS.apply));
    });

    it('falls back to default when env value is invalid', () => {
        const resolved = resolveShortcuts({ UI_SHORTCUTS_NEXT: 'shift+n' });
        expect(resolved.next).toEqual(parseShortcut(DEFAULT_SHORTCUTS.next));
    });

    it('covers every action with an env key', () => {
        expect(Object.keys(SHORTCUT_ENV_KEYS).sort()).toEqual(SHORTCUT_ACTIONS.map(a => a.action).sort());
    });
});

describe('pinned shortcut positions', () => {
    it('shows Alt+0 for the tenth pinned config', () => {
        expect(pinnedShortcutDisplay(1)).toBe('Alt+1');
        expect(pinnedShortcutDisplay(9)).toBe('Alt+9');
        expect(pinnedShortcutDisplay(10)).toBe('Alt+0');
    });

    it('maps the 0 key only to the tenth position', () => {
        expect(pinnedShortcutPosition('0')).toBe(10);
        expect(pinnedShortcutPosition('3')).toBe(3);
        expect(pinnedShortcutPosition('10')).toBeNull();
        expect(pinnedShortcutPosition('a')).toBeNull();
    });
});
