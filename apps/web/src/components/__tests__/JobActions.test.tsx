import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import JobActions from '../JobActions';
import { JobListParams } from '../../api/jobs';

describe('JobActions', () => {
    const mockProps = {
        job: { id: 123 } as any,
        filters: {} as JobListParams,
        onSeen: vi.fn(),
        onApplied: vi.fn(),
        onDiscarded: vi.fn(),
        onClosed: vi.fn(),
        onIgnore: vi.fn(),
        onNext: vi.fn(),
        onPrevious: vi.fn(),
        hasNext: true,
        hasPrevious: true,
    };

    beforeEach(() => {
        vi.clearAllMocks();
        // Mock clipboard
        Object.assign(navigator, {
            clipboard: {
                writeText: vi.fn(),
            },
        });
    });

    it('should render all buttons', () => {
        render(<JobActions {...mockProps} />);
        expect(screen.getByTitle('Mark as seen')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as applied')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as discarded')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as closed')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as ignored')).toBeInTheDocument();
        expect(screen.getByTitle('Copy permalink to clipboard')).toBeInTheDocument();
        expect(screen.getByTitle('Previous job')).toBeInTheDocument();
        expect(screen.getByTitle('Next job')).toBeInTheDocument();
    });

    it('should call callbacks on click', () => {
        render(<JobActions {...mockProps} />);
        
        fireEvent.click(screen.getByTitle('Mark as seen'));
        expect(mockProps.onSeen).toHaveBeenCalled();

        fireEvent.click(screen.getByTitle('Mark as applied'));
        expect(mockProps.onApplied).toHaveBeenCalled();
        
        fireEvent.click(screen.getByTitle('Next job'));
        expect(mockProps.onNext).toHaveBeenCalled();
    });

    it('should disable buttons when job is null', () => {
        render(<JobActions {...mockProps} job={null} />);
        
        expect(screen.getByTitle('Mark as seen')).toBeDisabled();
        expect(screen.getByTitle('Copy permalink to clipboard')).toBeDisabled();
        // Ignore should typically be enabled or disabled? Code says NO disabled prop for ignore-button usually? 
        // Let's check implementation: <button ... disabled={isBulk || !job}> for state buttons.
        // Wait, line 61: <button ... ignore-button ...>🚫</button> has NO disabled prop in the viewer.
        // Let's double check file content I read earlier.
        // Line 61: <button className="header-button state-button ignore-button" onClick={onIgnore} title="Mark as ignored">🚫</button>
        // Use 'Mark as seen' which definitely has disabled={isBulk || !job}
        
        expect(screen.getByTitle('Mark as seen')).toBeDisabled();
    });

    it('should disable nav buttons based on hasNext/hasPrevious', () => {
        render(<JobActions {...mockProps} hasNext={false} hasPrevious={false} />);
        expect(screen.getByTitle('Next job')).toBeDisabled();
        expect(screen.getByTitle('Previous job')).toBeDisabled();
    });

    it('should handle copy permalink with filters', () => {
        const filters = { search: 'dev', order: 'salary desc', days_old: 7 };
        render(<JobActions {...mockProps} filters={filters} />);
        
        fireEvent.click(screen.getByTitle('Copy permalink to clipboard'));
        
        expect(navigator.clipboard.writeText).toHaveBeenCalled();
        const calledUrl = (navigator.clipboard.writeText as any).mock.calls[0][0];
        expect(calledUrl).toContain('jobId=123');
        expect(calledUrl).toContain('search=dev');
        expect(calledUrl).toContain('order=salary+desc'); // URL encoded
        expect(calledUrl).toContain('days_old=7');
    });
});
