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

    it('displays new job count when provided', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} hasNewJobs={true} newJobsCount={5} />);
        
        // Use a function matcher because text is split across nodes
        expect(screen.getByText((content, element) => {
            return element?.tagName.toLowerCase() === 'button' && content.includes('List') && content.includes('(5 new)');
        })).toBeInTheDocument();
    });

    it('shows correct tooltip when new jobs are present', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="list" onTabChange={onTabChange} hasNewJobs={true} />);
        
        const listButton = screen.getByText((content, element) => element?.tagName.toLowerCase() === 'button' && content.includes('List'));
        expect(listButton).toHaveAttribute('title', 'Click to update list');
    });

    it('renders green dot when hasNewJobs is true', () => {
        const onTabChange = vi.fn();
        const { container } = render(<ViewTabs activeTab="list" onTabChange={onTabChange} hasNewJobs={true} />);
        
        expect(container.querySelector('.new-badge')).toBeInTheDocument();
    });

    it('calls onTabChange when clicked', () => {
        const onTabChange = vi.fn();
        render(<ViewTabs activeTab="edit" onTabChange={onTabChange} />);
        
        fireEvent.click(screen.getByText('List'));
        expect(onTabChange).toHaveBeenCalledWith('list');
    });
});
