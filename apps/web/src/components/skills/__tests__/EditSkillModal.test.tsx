import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EditSkillModal } from '../EditSkillModal';

const queryClient = new QueryClient();

const renderWithClient = (ui: React.ReactElement) => {
    return render(
        <QueryClientProvider client={queryClient}>
            {ui}
        </QueryClientProvider>
    );
};

describe('EditSkillModal', () => {
    const mockSkill = {
        name: 'React',
        description: 'Lib',
        learningPath: [],
    };


    it('renders with skill data in View mode by default', () => {
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        expect(screen.getByText('Skill: React')).toBeInTheDocument();
        expect(screen.getByText('Lib')).toBeInTheDocument(); // Description as text
    });

    it('should call onSave when Ctrl+Enter is pressed in Edit Mode', () => {
        const onSave = vi.fn();
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={onSave} onClose={vi.fn()} />);
        // Switch to Edit Mode first
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        
        fireEvent.keyDown(window, { key: 'Enter', ctrlKey: true });
        expect(onSave).toHaveBeenCalledTimes(1);
    });

    it('should call onSave when Meta+Enter is pressed in Edit Mode', () => {
        const onSave = vi.fn();
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={onSave} onClose={vi.fn()} />);
        // Switch to Edit Mode first
        fireEvent.click(screen.getByRole('button', { name: /Edit/i }));
        
        fireEvent.keyDown(window, { key: 'Enter', metaKey: true });
        expect(onSave).toHaveBeenCalledTimes(1);
    });

    it('opens existing skill in View mode by default', () => {
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        // Should show "Edit" button if in view mode
        expect(screen.getByRole('button', { name: /Edit/i })).toBeInTheDocument();
        // Should NOT show save button
        expect(screen.queryByText('Save Changes')).not.toBeInTheDocument();
    });

    it('switches to Edit mode when Edit button is clicked', () => {
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        
        const editBtn = screen.getByRole('button', { name: /Edit/i });
        fireEvent.click(editBtn);

        // Header should change
        expect(screen.getByText('Edit Skill: React')).toBeInTheDocument();
        
        // Description input should be visible (Name input is not visible for existing skills)
        expect(screen.getByDisplayValue('Lib')).toBeInTheDocument();
        // Save button should be visible
        expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });

    it('opens new skill in Edit mode by default', () => {
        const newSkill = { ...mockSkill, name: '' };
        renderWithClient(<EditSkillModal skill={newSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        
        expect(screen.getByText('Add New Skill')).toBeInTheDocument();
        // Should show Save button
        expect(screen.getByText('Create Skill')).toBeInTheDocument();
        // Should NOT have Edit button (already in edit mode)
        expect(screen.queryByRole('button', { name: /Edit/i })).not.toBeInTheDocument(); 
    });

    it('View mode displays database information (read-only)', () => {
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        
        // Should verify read-only elements are present
        expect(screen.getByText(/React/)).toBeInTheDocument();
        // Expect description to be rendered in markdown (or plain text if simple)
        expect(screen.getByText('Lib')).toBeInTheDocument();
    });

    it('toggles expand mode', () => {
        renderWithClient(<EditSkillModal skill={mockSkill} onSave={vi.fn()} onClose={vi.fn()} />);
        
        // Find the expand button (initially showing '↗' or title "Expand")
        const expandBtn = screen.getByTitle('Expand');
        expect(expandBtn).toBeInTheDocument();

        // Click to expand
        fireEvent.click(expandBtn);
        expect(screen.getByTitle('Collapse')).toBeInTheDocument();
        
        // Check if the modal content has the 'expanded' class
        // Note: verifying class presence on the specific element might be tricky with just screen queries unless we add a test-id or selecting by class. 
        // But we can check if the button state changed as a proxy for state update.
        // To be more precise, let's check the container.
        // We might need to add a data-testid to the modal-content in the main file if we want to be strict, 
        // but for now verifying the button title toggle is a good proxy that state updated.
    });
});


