import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import JobActions from '../JobActions';
import type { JobListParams } from '../../api/jobs';
import { ShortcutsContext, type ShortcutsContextValue } from '../../shortcutsContext';
import { defaultValue } from '../../shortcutsContext';

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

    const renderWithContext = (value: Partial<ShortcutsContextValue> = {}) => {
        const contextValue = { ...defaultValue(), ...value };
        return render(
            <ShortcutsContext.Provider value={contextValue}>
                <JobActions {...mockProps} />
            </ShortcutsContext.Provider>
        );
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
        expect(screen.getByTitle('Mark as applied — Alt+A')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as discarded')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as closed')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as ignored — Alt+I')).toBeInTheDocument();
        expect(screen.getByTitle('Copy permalink to clipboard')).toBeInTheDocument();
        expect(screen.getByTitle('Previous job — Alt+P')).toBeInTheDocument();
        expect(screen.getByTitle('Next job — Alt+N')).toBeInTheDocument();
    });

    it('should call callbacks on click', () => {
        render(<JobActions {...mockProps} />);
        
        fireEvent.click(screen.getByTitle('Mark as seen'));
        expect(mockProps.onSeen).toHaveBeenCalled();

        fireEvent.click(screen.getByTitle('Mark as applied — Alt+A'));
        expect(mockProps.onApplied).toHaveBeenCalled();
        
        fireEvent.click(screen.getByTitle('Next job — Alt+N'));
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
        expect(screen.getByTitle('Next job — Alt+N')).toBeDisabled();
        expect(screen.getByTitle('Previous job — Alt+P')).toBeDisabled();
    });

    it('should handle copy permalink with simplified jobId only', () => {
        const filters = { search: 'dev', order: 'salary desc', days_old: 7 };
        render(<JobActions {...mockProps} filters={filters} />);
        
        fireEvent.click(screen.getByTitle('Copy permalink to clipboard'));
        
        expect(navigator.clipboard.writeText).toHaveBeenCalled();
        const calledUrl = (navigator.clipboard.writeText as any).mock.calls[0][0];
        // Expect jobId to be present
        expect(calledUrl).toContain('jobId=123');
        // Expect other filters to be ABSENT, confirming simple permalink
        expect(calledUrl).not.toContain('search=dev');
        expect(calledUrl).not.toContain('order=salary');
        expect(calledUrl).not.toContain('days_old=7');
    });

    it('hides shortcut badges when modifier is not pressed', () => {
        renderWithContext({ modifierPressed: false });
        expect(screen.queryByText('Alt+I')).not.toBeInTheDocument();
        expect(screen.queryByText('Alt+A')).not.toBeInTheDocument();
    });

    it('shows shortcut badges only on shortcut-mapped buttons when modifier is held', () => {
        renderWithContext({ modifierPressed: true });
        expect(screen.getByText('Alt+I')).toBeInTheDocument();
        expect(screen.getByText('Alt+A')).toBeInTheDocument();
        expect(screen.getByText('Alt+P')).toBeInTheDocument();
        expect(screen.getByText('Alt+N')).toBeInTheDocument();
    });

    it('derives overlay badges from configured shortcuts', () => {
        const shortcuts = defaultValue().shortcuts;
        renderWithContext({ shortcuts: { ...shortcuts, ignore: { ctrl: true, alt: false, key: 'i', display: 'Ctrl+I' } }, modifierPressed: true });
        expect(screen.getByText('Ctrl+I')).toBeInTheDocument();
        expect(screen.getByTitle('Mark as ignored — Ctrl+I')).toBeInTheDocument();
    });
});
