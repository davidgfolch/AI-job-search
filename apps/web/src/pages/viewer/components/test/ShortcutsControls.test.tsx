import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ShortcutsControls from '../ShortcutsControls';
import { resolveShortcuts, SHORTCUT_ACTIONS } from '../../shortcutsConfig';

describe('ShortcutsControls', () => {
    const shortcuts = resolveShortcuts(undefined);

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders toggle and help buttons', () => {
        render(<ShortcutsControls enabled={true} onToggle={vi.fn()} shortcuts={shortcuts} />);
        expect(screen.getByTitle('Keyboard shortcuts enabled')).toBeInTheDocument();
        expect(screen.getByTitle('Show keyboard shortcuts')).toBeInTheDocument();
    });

    it('reflects disabled state in the toggle button', () => {
        render(<ShortcutsControls enabled={false} onToggle={vi.fn()} shortcuts={shortcuts} />);
        const toggle = screen.getByTitle('Keyboard shortcuts disabled');
        expect(toggle).toHaveAttribute('aria-pressed', 'false');
    });

    it('calls onToggle when toggle button is clicked', () => {
        const onToggle = vi.fn();
        render(<ShortcutsControls enabled={true} onToggle={onToggle} shortcuts={shortcuts} />);
        fireEvent.click(screen.getByTitle('Keyboard shortcuts enabled'));
        expect(onToggle).toHaveBeenCalled();
    });

    it('shows the shortcut list in the help modal', () => {
        render(<ShortcutsControls enabled={true} onToggle={vi.fn()} shortcuts={shortcuts} />);
        fireEvent.click(screen.getByTitle('Show keyboard shortcuts'));
        expect(screen.getByText('Keyboard shortcuts')).toBeInTheDocument();
        for (const info of SHORTCUT_ACTIONS) {
            expect(screen.getByText(info.label)).toBeInTheDocument();
            expect(screen.getByText(shortcuts[info.action].display)).toBeInTheDocument();
        }
    });

    it('closes the help modal', () => {
        render(<ShortcutsControls enabled={true} onToggle={vi.fn()} shortcuts={shortcuts} />);
        fireEvent.click(screen.getByTitle('Show keyboard shortcuts'));
        fireEvent.keyDown(window, { key: 'Escape' });
        expect(screen.queryByText('Keyboard shortcuts')).not.toBeInTheDocument();
    });

    it('shows pinned configuration shortcuts with position', () => {
        const pinnedShortcuts = [
            { name: 'By company', index: 1 },
            { name: 'Remote', index: 2 },
        ];
        render(<ShortcutsControls enabled={true} onToggle={vi.fn()} shortcuts={shortcuts} pinnedShortcuts={pinnedShortcuts} />);
        fireEvent.click(screen.getByTitle('Show keyboard shortcuts'));
        expect(screen.getByText('Load pinned filters:')).toBeInTheDocument();
        expect(screen.getByText('By company')).toBeInTheDocument();
        expect(screen.getByText('Remote')).toBeInTheDocument();
        expect(screen.getByText('Alt+1')).toBeInTheDocument();
        expect(screen.getByText('Alt+2')).toBeInTheDocument();
    });
});
