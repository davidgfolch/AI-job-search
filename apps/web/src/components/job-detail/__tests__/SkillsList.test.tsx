import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SkillsList from '../SkillsList';
import * as useLearnListHook from '../../skills/useLearnList';

// Mock the EditSkillModal to avoid rendering the complex modal and simplify testing
vi.mock('../../skills/EditSkillModal', () => ({
    EditSkillModal: ({ skill, onSave, onClose }: any) => (
        <div data-testid="edit-skill-modal">
            <span data-testid="modal-skill-name">{skill.name}</span>
            <button onClick={() => onSave({ description: 'New Desc', learningPath: ['link1'] })}>Save</button>
            <button onClick={onClose}>Close</button>
        </div>
    ),
}));

describe('SkillsList', () => {
    const mockSaveSkill = vi.fn();
    const mockToggleSkill = vi.fn();
    const mockIsInLearnList = vi.fn();
    const mockLearnList = [
        { name: 'React', description: 'React Desc', learningPath: [], disabled: false },
        { name: 'Node.js', description: 'Node Desc', learningPath: [], disabled: false }
    ];

    beforeEach(() => {
        vi.resetAllMocks();
        // Mock the return value of useLearnList
        vi.spyOn(useLearnListHook, 'useLearnList').mockReturnValue({
            learnList: mockLearnList,
            saveSkill: mockSaveSkill,
            toggleSkill: mockToggleSkill,
            isInLearnList: mockIsInLearnList,
            skillExists: (skillName: string) => 
                mockLearnList.find(s => s.name.toLowerCase() === skillName.trim().toLowerCase()),
            reorderSkills: vi.fn(),
            removeSkill: vi.fn(),
            updateSkill: vi.fn(),
            isLoading: false,
            error: null,
            fetchSkills: vi.fn(),
        });
    });

    it('renders list of skills', () => {
        render(<SkillsList skills="React, TypeScript, Node.js" />);
        
        expect(screen.getByText('React')).toBeInTheDocument();
        expect(screen.getByText('TypeScript')).toBeInTheDocument();
        expect(screen.getByText('Node.js')).toBeInTheDocument();
    });

    it('does not render modal initially', () => {
        render(<SkillsList skills="React" />);
        expect(screen.queryByTestId('edit-skill-modal')).not.toBeInTheDocument();
    });

    it('opens modal when view detail button is clicked for existing skill', () => {
        // Mock isInLearnList to return true for React
        mockIsInLearnList.mockReturnValue(true);
        render(<SkillsList skills="React" />);
        
        // Find the view detail button
        const viewBtn = screen.getByText('👁');
        fireEvent.click(viewBtn);

        expect(screen.getByTestId('edit-skill-modal')).toBeInTheDocument();
        expect(screen.getByTestId('modal-skill-name')).toHaveTextContent('React'); 
    });

    it('does not show view detail button for skill not in learn list', () => {
        // Mock isInLearnList to return false for NewSkill
        mockIsInLearnList.mockReturnValue(false);
        render(<SkillsList skills="NewSkill" />);
        
        expect(screen.queryByText('👁')).not.toBeInTheDocument();
    });

    it('calls saveSkill when save is triggered in modal', () => {
        mockIsInLearnList.mockReturnValue(true);
        render(<SkillsList skills="React" />);
        
        // Open modal
        fireEvent.click(screen.getByText('👁'));
        
        // Click save in mock modal
        fireEvent.click(screen.getByText('Save'));

        expect(mockSaveSkill).toHaveBeenCalledWith(expect.objectContaining({
            name: 'React',
            description: 'New Desc',
            learningPath: ['link1']
        }));
        
        // Modal should close (or at least state update, checking if it renders null might require rerender or waitFor if it was async, but here it's sync state update)
        expect(screen.queryByTestId('edit-skill-modal')).not.toBeInTheDocument();
    });

    it('closes modal when close is triggered', () => {
        mockIsInLearnList.mockReturnValue(true);
        render(<SkillsList skills="React" />);
        
        // Open modal
        fireEvent.click(screen.getByText('👁'));
        expect(screen.getByTestId('edit-skill-modal')).toBeInTheDocument();
        
        // Click close in mock modal
        fireEvent.click(screen.getByText('Close'));
        
        expect(screen.queryByTestId('edit-skill-modal')).not.toBeInTheDocument();
    });
});
