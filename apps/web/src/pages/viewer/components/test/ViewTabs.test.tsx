
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ViewTabs from '../ViewTabs';

describe('ViewTabs', () => {
    it('renders tabs correctly', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} />);
        
        expect(screen.getByText('List')).toBeInTheDocument();
        expect(screen.getByText('Edit')).toBeInTheDocument();
        expect(screen.getByText('Create')).toBeInTheDocument();
    });

    it('calls onTabChange when a tab is clicked', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} />);
        
        fireEvent.click(screen.getByText('Edit'));
        expect(onTabChange).toHaveBeenCalledWith('edit');
    });

    it('highlights the active tab', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="create" onTabChange={onTabChange} />);
        
        const createTab = screen.getByText('Create');
        expect(createTab).toHaveClass('active');
        
        const listTab = screen.getByText('List');
        expect(listTab).not.toHaveClass('active');
    });
});
