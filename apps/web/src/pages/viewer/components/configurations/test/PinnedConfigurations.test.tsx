import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PinnedConfigurations } from '../PinnedConfigurations';
import { ShortcutsContext, defaultValue } from '../../../shortcutsContext';
import type { FilterConfig } from '../hooks/useFilterConfigurations';

describe('PinnedConfigurations', () => {
    const pinnedConfigs: FilterConfig[] = [
        { name: 'By company', filters: {} },
        { name: 'Clean - Delete old jobs', filters: {} },
    ];

    const renderWithContext = (modifierPressed = false) =>
        render(
            <ShortcutsContext.Provider value={{ ...defaultValue(), modifierPressed }}>
                <PinnedConfigurations pinnedConfigs={pinnedConfigs} onLoad={vi.fn()} onUnpin={vi.fn()} />
            </ShortcutsContext.Provider>
        );

    it('renders pinned config buttons with shortcut tooltips', () => {
        renderWithContext();
        expect(screen.getByTitle('Load: By company — Alt+1')).toBeInTheDocument();
        expect(screen.getByTitle('Load: Clean - Delete old jobs — Alt+2')).toBeInTheDocument();
    });

    it('shows Alt shortcut badges when modifier is held', () => {
        renderWithContext(true);
        expect(screen.getAllByText('Alt+1').length).toBeGreaterThan(0);
        expect(screen.getByText('Alt+2')).toBeInTheDocument();
    });

    it('hides Alt shortcut badges by default', () => {
        renderWithContext(false);
        expect(screen.queryByText('Alt+2')).not.toBeInTheDocument();
    });

    it('calls onLoad when a pinned config is clicked', () => {
        const onLoad = vi.fn();
        render(
            <PinnedConfigurations pinnedConfigs={pinnedConfigs} onLoad={onLoad} onUnpin={vi.fn()} />
        );
        fireEvent.click(screen.getByTitle('Load: By company — Alt+1'));
        expect(onLoad).toHaveBeenCalledWith(pinnedConfigs[0]);
    });

    it('does not render when there are no pinned configs', () => {
        const { container } = render(
            <PinnedConfigurations pinnedConfigs={[]} onLoad={vi.fn()} onUnpin={vi.fn()} />
        );
        expect(container).toBeEmptyDOMElement();
    });
});