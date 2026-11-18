import { render, screen, fireEvent } from '@testing-library/react';
import type { ComponentProps } from 'react';
import { describe, it, expect, vi } from 'vitest';
import ViewTabs from '../ViewTabs';

describe('ViewTabs', () => {
    const renderTabs = (props: Partial<ComponentProps<typeof ViewTabs>> = {}) => {
        const onTabChange = vi.fn();
        const onReload = vi.fn();
        const onDelete = vi.fn();
        const result = render(<ViewTabs activeTab="list" onTabChange={onTabChange} onReload={onReload} onDelete={onDelete} {...props} />);
        return { onTabChange, onReload, onDelete, ...result };
    };

    it('renders tabs with accessible names', () => {
        renderTabs();
        expect(screen.getByRole('button', { name: 'List view' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Edit view' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Create view' })).toBeInTheDocument();
        expect(screen.getByText('List')).toBeInTheDocument();
        expect(screen.getByText('Edit')).toBeInTheDocument();
        expect(screen.getByText('Create')).toBeInTheDocument();
    });

    it('renders an icon alongside each label', () => {
        const { container } = renderTabs();
        expect(container.querySelector('#tab-button-list .tab-icon')?.textContent).toBe('📋');
        expect(container.querySelector('#tab-button-edit .tab-icon')?.textContent).toBe('✏️');
        expect(container.querySelector('#tab-button-create .tab-icon')?.textContent).toBe('➕');
    });

    it.each([
        ['List view', 'list'],
        ['Edit view', 'edit'],
        ['Create view', 'create'],
    ])('calls onTabChange with %s when clicked', (name, tab) => {
        const { onTabChange } = renderTabs({ activeTab: 'edit' });
        fireEvent.click(screen.getByRole('button', { name }));
        expect(onTabChange).toHaveBeenCalledWith(tab);
    });

    it('highlights the active tab', () => {
        renderTabs({ activeTab: 'create' });
        expect(screen.getByRole('button', { name: 'Create view' })).toHaveClass('active');
        expect(screen.getByRole('button', { name: 'List view' })).not.toHaveClass('active');
    });

    it('renders reload button when hasNewJobs is true', () => {
        const { onReload } = renderTabs({ hasNewJobs: true, newJobsCount: 5 });
        expect(screen.getByText('5 new')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Click to reload list' }));
        expect(onReload).toHaveBeenCalled();
    });

    it('renders delete button when hasSelection is true and onDelete provided', () => {
        const { onDelete } = renderTabs({ hasSelection: true, selectedCount: 3 });
        expect(screen.getByText('Delete (3)')).toBeInTheDocument();
        fireEvent.click(screen.getByRole('button', { name: 'Delete selected jobs' }));
        expect(onDelete).toHaveBeenCalledWith(3);
    });
});
