export type ShortcutAction = 'ignore' | 'apply' | 'next' | 'previous' | 'openUrl' | 'listFocus' | 'detailFocus';

export interface ShortcutActionInfo {
    action: ShortcutAction;
    label: string;
    description: string;
}

export interface ShortcutCombo {
    ctrl: boolean;
    alt: boolean;
    key: string;
    display: string;
}

export const SHORTCUT_ACTIONS: ShortcutActionInfo[] = [
    { action: 'ignore', label: 'Ignore job', description: 'Mark selected job as ignored' },
    { action: 'apply', label: 'Apply job', description: 'Open the apply modal for the selected job' },
    { action: 'next', label: 'Next job', description: 'Select the next job in the list' },
    { action: 'previous', label: 'Previous job', description: 'Select the previous job in the list' },
    { action: 'openUrl', label: 'Open job URL', description: 'Open the selected job link in a new tab' },
    { action: 'listFocus', label: 'List scroll focus', description: 'Focus the jobs list to scroll with arrow keys' },
    { action: 'detailFocus', label: 'Job detail scroll focus', description: 'Focus the job detail to scroll with arrow keys' },
];

export const DEFAULT_SHORTCUTS: Record<ShortcutAction, string> = {
    ignore: 'alt+i',
    apply: 'alt+a',
    next: 'alt+n',
    previous: 'alt+p',
    openUrl: 'alt+o',
    listFocus: 'alt+l',
    detailFocus: 'alt+j',
};

export const SHORTCUT_ENV_KEYS: Record<ShortcutAction, string> = {
    ignore: 'UI_SHORTCUTS_IGNORE',
    apply: 'UI_SHORTCUTS_APPLY',
    next: 'UI_SHORTCUTS_NEXT',
    previous: 'UI_SHORTCUTS_PREVIOUS',
    openUrl: 'UI_SHORTCUTS_OPEN_URL',
    listFocus: 'UI_SHORTCUTS_LIST_FOCUS',
    detailFocus: 'UI_SHORTCUTS_DETAIL_FOCUS',
};

export const UI_SHORTCUTS_ENABLED_KEY = 'UI_SHORTCUTS_ENABLED';
export const UI_SHORTCUTS_STORAGE_KEY = 'ui_shortcuts_enabled';

export function parseShortcut(value: string | undefined): ShortcutCombo | null {
    if (!value) return null;
    const parts = value.trim().toLowerCase().split('+');
    if (parts.length !== 2) return null;
    const [modifier, key] = parts;
    if (modifier !== 'ctrl' && modifier !== 'alt') return null;
    if (key.length !== 1) return null;
    const ctrl = modifier === 'ctrl';
    return { ctrl, alt: !ctrl, key, display: `${modifier.charAt(0).toUpperCase()}${modifier.slice(1)}+${key.toUpperCase()}` };
}

export const titleWithShortcut = (description: string, combo: ShortcutCombo): string => `${description} — ${combo.display}`;

export function resolveShortcuts(envSettings: Record<string, string> | undefined): Record<ShortcutAction, ShortcutCombo> {
    const result = {} as Record<ShortcutAction, ShortcutCombo>;
    for (const info of SHORTCUT_ACTIONS) {
        const envKey = SHORTCUT_ENV_KEYS[info.action];
        const parsed = parseShortcut(envSettings?.[envKey]) ?? parseShortcut(DEFAULT_SHORTCUTS[info.action]);
        result[info.action] = parsed as ShortcutCombo;
    }
    return result;
}
