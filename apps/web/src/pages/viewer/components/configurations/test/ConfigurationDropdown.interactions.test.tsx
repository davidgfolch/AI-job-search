import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ConfigurationDropdown } from '../ConfigurationDropdown';
import type { FilterConfig } from '../hooks/useFilterConfigurations';

const config = (name: string, over: Partial<FilterConfig> = {}): FilterConfig => ({ name, filters: {} as any, ...over });

describe('ConfigurationDropdown interactions', () => {
    let props: any;

    beforeEach(() => {
        props = {
            isOpen: true,
            filteredConfigs: [config('JVM Spring'), config('Clean', { watched: true, statistics: false, pinned: true })],
            highlightIndex: -1,
            onLoad: vi.fn(), onDelete: vi.fn(), setHighlightIndex: vi.fn(),
            onToggleWatch: vi.fn(), onToggleStats: vi.fn(), onTogglePin: vi.fn(),
        };
    });

    const drag = (el: Element, type: 'dragStart' | 'dragEnter' | 'dragOver' | 'drop') =>
        fireEvent[type](el, { dataTransfer: { effectAllowed: '', dropEffect: '' } });

    it('loads a configuration when its row is clicked', () => {
        render(<ConfigurationDropdown {...props} />);
        fireEvent.click(screen.getByText('JVM Spring'));
        expect(props.onLoad).toHaveBeenCalledWith(props.filteredConfigs[0]);
    });

    it('highlights the hovered row', () => {
        render(<ConfigurationDropdown {...props} />);
        fireEvent.mouseEnter(screen.getByText('Clean').closest('li') as HTMLElement);
        expect(props.setHighlightIndex).toHaveBeenCalledWith(1);
    });

    it('marks only the highlighted row active', () => {
        const { container } = render(<ConfigurationDropdown {...props} highlightIndex={1} />);
        const rows = container.querySelectorAll('li');
        expect(rows[0]).not.toHaveClass('active');
        expect(rows[1]).toHaveClass('active');
    });

    it.each([
        ['pin', 'Pin configuration', 'onTogglePin'],
        ['statistics', 'Exclude from Statistics', 'onToggleStats'],
        ['watch', 'Watch', 'onToggleWatch'],
    ])('toggles %s for the row without loading it', (_label, title, handler) => {
        render(<ConfigurationDropdown {...props} />);
        fireEvent.click(screen.getAllByTitle(title)[0]);
        expect(props[handler]).toHaveBeenCalledWith('JVM Spring');
        expect(props.onLoad).not.toHaveBeenCalled();
    });

    it.each([
        ['pinned config', 'Unpin configuration', 'enabled'],
        ['unpinned config', 'Pin configuration', 'disabled'],
        ['statistics disabled', 'Include in Statistics', 'disabled'],
        ['statistics enabled', 'Exclude from Statistics', 'enabled'],
        ['watched config', 'Unwatch', 'enabled'],
        ['unwatched config', 'Watch', 'disabled'],
    ])('reflects the %s state in the button class', (_label, title, cls) => {
        render(<ConfigurationDropdown {...props} />);
        expect(screen.getAllByTitle(title)[0]).toHaveClass('config-toggle-btn', cls);
    });

    it('shows the statistics-off icon when statistics are disabled', () => {
        render(<ConfigurationDropdown {...props} />);
        expect(screen.getAllByTitle('Include in Statistics')[0]).toHaveTextContent('📉');
        expect(screen.getAllByTitle('Exclude from Statistics')[0]).toHaveTextContent('📈');
    });

    it('prevents the default mousedown on the toggle buttons so the row is not loaded', () => {
        render(<ConfigurationDropdown {...props} />);
        expect(fireEvent.mouseDown(screen.getAllByTitle('Delete configuration')[0])).toBe(false);
        expect(props.onLoad).not.toHaveBeenCalled();
    });

    it('deletes the configuration with the originating event', () => {
        render(<ConfigurationDropdown {...props} />);
        fireEvent.click(screen.getAllByTitle('Delete configuration')[0]);
        expect(props.onDelete).toHaveBeenCalledWith('JVM Spring', expect.objectContaining({ type: 'click' }));
    });

    it('shows the watcher badge and tooltip only when a watcher result exists', () => {
        const { container, rerender } = render(<ConfigurationDropdown {...props} />);
        expect(screen.queryByText('+3')).not.toBeInTheDocument();
        rerender(<ConfigurationDropdown {...props} results={{ 'JVM Spring': { total: 10, newItems: 3 } as any }} lastCheckTime={new Date('2026-01-01T10:00:00')} />);
        expect(screen.getByText('+3')).toBeInTheDocument();
        expect(container.querySelectorAll('li')[0]).toHaveAttribute('title', expect.stringContaining('Total: 10 | New: 3'));
    });

    it('reorders the list when a row is dragged onto another', () => {
        const onReorder = vi.fn();
        const { container } = render(<ConfigurationDropdown {...props} onReorder={onReorder} allowReorder />);
        const rows = container.querySelectorAll('li');
        drag(rows[0], 'dragStart');
        drag(rows[1], 'dragEnter');
        drag(rows[1], 'dragOver');
        drag(rows[1], 'drop');
        expect(onReorder).toHaveBeenCalledWith([props.filteredConfigs[1], props.filteredConfigs[0]]);
    });

    it('ignores a drop onto the same row', () => {
        const onReorder = vi.fn();
        const { container } = render(<ConfigurationDropdown {...props} onReorder={onReorder} allowReorder />);
        const rows = container.querySelectorAll('li');
        drag(rows[0], 'dragStart');
        drag(rows[0], 'dragEnter');
        drag(rows[0], 'drop');
        expect(onReorder).not.toHaveBeenCalled();
    });

    it('ignores a drop when no drag was ever started', () => {
        const onReorder = vi.fn();
        const { container } = render(<ConfigurationDropdown {...props} onReorder={onReorder} allowReorder />);
        const rows = container.querySelectorAll('li');
        drag(rows[1], 'dragEnter');
        drag(rows[1], 'drop');
        expect(onReorder).not.toHaveBeenCalled();
    });

    it('marks rows as draggable only when reordering is allowed', () => {
        const { container, rerender } = render(<ConfigurationDropdown {...props} />);
        expect(container.querySelector('li')).toHaveAttribute('draggable', 'false');
        rerender(<ConfigurationDropdown {...props} allowReorder />);
        expect(container.querySelector('li')).toHaveAttribute('draggable', 'true');
    });
});