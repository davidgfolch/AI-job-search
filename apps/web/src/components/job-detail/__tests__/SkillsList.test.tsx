import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SkillsList from '../SkillsList';
import * as useLearnListHook from '../../skills/useLearnList';

// Mock the EditSkillModal to avoid rendering the complex modal and simplify testing
vi.mock('../../skills/EditSkillModal', () => ({
    EditSkillModal: ({ skill, onSave, onClose, onNext, onPrevious, hasNext, hasPrevious }: any) => (
        <div data-testid="edit-skill-modal">
            <span data-testid="modal-skill-name">{skill.name}</span>
            <button onClick={() => onSave({ description: 'New Desc', learningPath: ['link1'] })}>Save</button>
            <button onClick={onClose}>Close</button>
            <button onClick={onNext} disabled={!hasNext} data-testid="next-btn">Next</button>
            <button onClick={onPrevious} disabled={!hasPrevious} data-testid="prev-btn">Previous</button>
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

    it('shows view detail button only for database skills', () => {
        // Mock isInLearnList to return false for NewSkill
        mockIsInLearnList.mockReturnValue(false);
        render(<SkillsList skills="NewSkill" />);
        expect(screen.queryByText('👁')).not.toBeInTheDocument();

        // Mock isInLearnList to return true for React
        mockIsInLearnList.mockReturnValue(true);
        render(<SkillsList skills="React" />);
        expect(screen.getByText('👁')).toBeInTheDocument();
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

    it('navigates through database skills with case-insensitivity and unique normalized names', () => {
        // Setup: React and Node.js exist in database with different casing. 
        // BSM also exists.
        const dbSkills = [
            { name: 'react', description: 'React Desc', learningPath: [], disabled: false },
            { name: 'Node.js', description: 'Node Desc', learningPath: [], disabled: false },
            { name: 'bsm', description: 'BSM Desc', learningPath: [], disabled: false }
        ];
        
        vi.spyOn(useLearnListHook, 'useLearnList').mockReturnValue({
            learnList: dbSkills,
            saveSkill: mockSaveSkill,
            toggleSkill: mockToggleSkill,
            isInLearnList: (name: string) => dbSkills.some(s => s.name.toLowerCase() === name.toLowerCase()),
            skillExists: (skillName: string) => 
                dbSkills.find(s => s.name.toLowerCase() === skillName.trim().toLowerCase()),
            reorderSkills: vi.fn(),
            removeSkill: vi.fn(),
            updateSkill: vi.fn(),
            isLoading: false,
            error: null,
            fetchSkills: vi.fn(),
        } as any);

        render(<SkillsList 
            skills="React" 
            allJobSkills="React, Jenkins, Node.js, BSM, bsm" 
        />);
        
        // Open React (which exists as 'react' in DB)
        fireEvent.click(screen.getByText('👁')); 
        expect(screen.getByTestId('modal-skill-name')).toHaveTextContent('react');
        
        const nextBtn = screen.getByTestId('next-btn');
        const prevBtn = screen.getByTestId('prev-btn');

        // Initial state: React
        expect(prevBtn).toBeDisabled();
        expect(nextBtn).not.toBeDisabled();
        
        // Click Next - Should go to Node.js (skipping Jenkins since it's not in database)
        fireEvent.click(nextBtn);
        expect(screen.getByTestId('modal-skill-name')).toHaveTextContent('Node.js');
        expect(prevBtn).not.toBeDisabled();
        expect(nextBtn).not.toBeDisabled();

        // Click Next - Should go to BSM (even if it was listed twice in job, it should be unique)
        fireEvent.click(nextBtn);
        expect(screen.getByTestId('modal-skill-name')).toHaveTextContent('bsm');
        expect(nextBtn).toBeDisabled();
        expect(prevBtn).not.toBeDisabled();

        // Click Previous - Should go back to Node.js
        fireEvent.click(prevBtn);
        expect(screen.getByTestId('modal-skill-name')).toHaveTextContent('Node.js');
    });
});
