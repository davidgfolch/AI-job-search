
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ViewTabs from '../ViewTabs';

describe('ViewTabs', () => {
    it('renders tabs correctly', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} />);
        
        expect(screen.getByText('List')).toBeInTheDocument();
        expect(screen.getByText('Edit')).toBeInTheDocument();
    });

    it('displays new job button when provided', () => {
        const onTabChange = vi.fn();
        const onReload = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} hasNewJobs={true} newJobsCount={5} onReload={onReload} />);
        
        // Check for separate list button
        expect(screen.getByText('List')).toBeInTheDocument();
        
        // Check for new button
        const newButton = screen.getByText((content, element) => {
             return element?.tagName.toLowerCase() === 'button' && content.includes('5 new');
        });
        expect(newButton).toBeInTheDocument();
        expect(newButton).toHaveClass('has-new-jobs');
    });

    it('calls onReload when new button is clicked', () => {
        const onTabChange = vi.fn();
        const onReload = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} hasNewJobs={true} newJobsCount={5} onReload={onReload} />);
        
        const newButton = screen.getByText((content, element) => {
             return element?.tagName.toLowerCase() === 'button' && content.includes('5 new');
        });
        
        fireEvent.click(newButton);
        expect(onReload).toHaveBeenCalled();
        expect(onTabChange).not.toHaveBeenCalled();
    });


    it('calls onTabChange when List is clicked', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="edit" onTabChange={onTabChange} />);
        
        fireEvent.click(screen.getByText('List'));
        expect(onTabChange).toHaveBeenCalledWith('list');
    });
});
