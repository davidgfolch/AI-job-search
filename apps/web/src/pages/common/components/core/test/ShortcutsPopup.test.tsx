import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ShortcutsPopup from '../ShortcutsPopup';

const shortcuts = [
    { label: 'Ignore job', description: 'Mark selected job as ignored', display: 'Alt+I' },
    { label: 'Next job', description: 'Select the next job', display: 'Alt+N' },
];
const pinnedShortcuts = [{ name: 'By company', display: 'Alt+1' }];

describe('ShortcutsPopup', () => {
    it('shows the enabled state in the header toggle', () => {
        render(<ShortcutsPopup isOpen={true} onClose={vi.fn()} enabled={true} onToggle={vi.fn()} shortcuts={shortcuts} />);
        expect(screen.getByText('Keyboard shortcuts')).toBeInTheDocument();
        expect(screen.getByTitle('Keyboard shortcuts enabled')).toHaveAttribute('aria-checked', 'true');
    });

    it('reflects the disabled state in the header toggle', () => {
        render(<ShortcutsPopup isOpen={true} onClose={vi.fn()} enabled={false} onToggle={vi.fn()} shortcuts={shortcuts} />);
        expect(screen.getByTitle('Keyboard shortcuts disabled')).toHaveAttribute('aria-checked', 'false');
    });

    it('calls onToggle from the header toggle', () => {
        const onToggle = vi.fn();
        render(<ShortcutsPopup isOpen={true} onClose={vi.fn()} enabled={true} onToggle={onToggle} shortcuts={shortcuts} />);
        fireEvent.click(screen.getByTitle('Keyboard shortcuts enabled'));
        expect(onToggle).toHaveBeenCalledOnce();
    });

    it('lists shortcuts and pinned shortcuts', () => {
        render(<ShortcutsPopup isOpen={true} onClose={vi.fn()} enabled={true} onToggle={vi.fn()} shortcuts={shortcuts} pinnedShortcuts={pinnedShortcuts} />);
        expect(screen.getByText('Load pinned filters:')).toBeInTheDocument();
        for (const shortcut of shortcuts) {
            expect(screen.getByText(shortcut.label)).toBeInTheDocument();
            expect(screen.getByText(shortcut.display)).toBeInTheDocument();
        }
        expect(screen.getByText('By company')).toBeInTheDocument();
        expect(screen.getByText('Alt+1')).toBeInTheDocument();
    });

    it('requests close on Escape', () => {
        const onClose = vi.fn();
        render(<ShortcutsPopup isOpen={true} onClose={onClose} enabled={true} onToggle={vi.fn()} shortcuts={shortcuts} />);
        fireEvent.keyDown(window, { key: 'Escape' });
        expect(onClose).toHaveBeenCalledOnce();
    });
});
