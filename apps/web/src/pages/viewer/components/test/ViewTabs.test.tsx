
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
    it('calls onTabChange with list when List tab is clicked', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="edit" onTabChange={onTabChange} />);
        
        fireEvent.click(screen.getByText('List'));
        expect(onTabChange).toHaveBeenCalledWith('list');
    });

    it('calls onTabChange with create when Create tab is clicked', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} />);
        
        fireEvent.click(screen.getByText('Create'));
        expect(onTabChange).toHaveBeenCalledWith('create');
    });

    it('renders reload button when hasNewJobs is true', () => {
        const onTabChange = vi.fn();
        const onReload = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} hasNewJobs={true} newJobsCount={5} onReload={onReload} />);
        
        const reloadBtn = screen.getByText(/5 new/);
        expect(reloadBtn).toBeInTheDocument();
        fireEvent.click(reloadBtn);
        expect(onReload).toHaveBeenCalled();
    });

    it('renders delete button when hasSelection is true and onDelete provided', () => {
        const onTabChange = vi.fn();
        const onDelete = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} hasSelection={true} selectedCount={3} onDelete={onDelete} />);
        
        const deleteBtn = screen.getByText(/Delete \(3\)/);
        expect(deleteBtn).toBeInTheDocument();
        fireEvent.click(deleteBtn);
        expect(onDelete).toHaveBeenCalledWith(3);
    });
});
