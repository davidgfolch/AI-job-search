import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SkillsManager from '../SkillsManager';
import * as useLearnListHook from '../../components/skills/useLearnList';
import { 
    initialSkills, 
    setupLearnListMock, 
    mockReorderSkills, 
    mockRemoveSkill, 
    mockSaveSkill,
    mockUpdateSkill,
    MockEditSkillModal 
} from './SkillsManager.test.utils';

// Mock the hook
vi.mock('../../components/skills/useLearnList', () => ({
  useLearnList: vi.fn(),
}));

// Mock the Modal
vi.mock('../../components/skills/EditSkillModal', () => ({
  EditSkillModal: (props: any) => MockEditSkillModal(props)
}));

describe('SkillsManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupLearnListMock(useLearnListHook);
    vi.spyOn(window, 'confirm').mockImplementation(() => true);
  });

  describe('Rendering', () => {
    it.each([
        ['filled', initialSkills, 'React', true],
        ['empty', [], 'No skills in your learn list yet', false]
    ])('renders %s state correctly', (_, skills, expectedText, hasTable) => {
        setupLearnListMock(useLearnListHook, skills);
        render(<SkillsManager />);
        expect(screen.getByText(new RegExp(expectedText, 'i'))).toBeInTheDocument();
        if (hasTable) {
            expect(screen.getByRole('table')).toBeInTheDocument();
        } else {
            expect(screen.queryByRole('table')).not.toBeInTheDocument();
        }
    });

    it('toggles between table and markdown view', () => {
        render(<SkillsManager />);
        const toggleButton = screen.getByText('View MD');
        
        // Initial State
        expect(toggleButton).toBeInTheDocument();
        expect(screen.getByRole('table')).toBeInTheDocument();
        
        // Switch to MD
        fireEvent.click(toggleButton);
        expect(screen.getByText('View Table')).toBeInTheDocument();
        expect(screen.queryByRole('table')).not.toBeInTheDocument();
        expect(screen.getByRole('heading', { level: 1, name: /My Skills/i })).toBeInTheDocument();
        
        // Switch back
        fireEvent.click(screen.getByText('View Table'));
        expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
      it('calls reorderSkills when dragging and dropping', () => {
        render(<SkillsManager />);
        const rows = screen.getAllByRole('row');
        // Source: React (index 1), Target: TypeScript (index 2)
        const [sourceRow, targetRow] = [rows[1], rows[2]]; 
        const mockDataTransfer = { effectAllowed: '', dropEffect: '' };
        
        fireEvent.dragStart(sourceRow, { dataTransfer: mockDataTransfer });
        fireEvent.dragOver(targetRow, { dataTransfer: mockDataTransfer });
        fireEvent.drop(targetRow, { dataTransfer: mockDataTransfer });
        
        expect(mockReorderSkills).toHaveBeenCalled();
        expect(mockReorderSkills.mock.calls[0][0]).toHaveLength(3);
      });

      it('calls removeSkill when delete button is clicked and confirmed', () => {
        render(<SkillsManager />);
        fireEvent.click(screen.getAllByTitle('Remove Skill')[0]);
        expect(window.confirm).toHaveBeenCalled();
        expect(mockRemoveSkill).toHaveBeenCalledWith('React');
      });
  });

  describe('Modal Operations', () => {
      it('opens modal on edit click and saves changes', () => {
        // Setup with one skill
        setupLearnListMock(useLearnListHook, [initialSkills[0]]); 
        render(<SkillsManager />);
        
        fireEvent.click(screen.getByTitle('Edit Skill'));
        
        const textarea = screen.getByDisplayValue('Frontend Lib');
        fireEvent.change(textarea, { target: { value: 'New Desc' } });
        fireEvent.click(screen.getByText('Save Changes'));
        
        expect(mockSaveSkill).toHaveBeenCalledWith(expect.objectContaining({
          name: 'React',
          description: 'New Desc'
        }));
      });

      it('opens modal on add skill click and creates new skill', () => {
        setupLearnListMock(useLearnListHook, []);
        render(<SkillsManager />);

        fireEvent.click(screen.getByText('+ Add Skill'));
        
        fireEvent.change(screen.getByPlaceholderText('Skill Name'), { target: { value: 'New Skill' } });
        fireEvent.click(screen.getByText('Create Skill'));

        expect(mockSaveSkill).toHaveBeenCalledWith(expect.objectContaining({
          name: 'New Skill',
          description: ''
        }));
      });
  });
});
