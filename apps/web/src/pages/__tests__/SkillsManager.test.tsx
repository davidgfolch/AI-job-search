import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SkillsManager from '../SkillsManager';
import * as useLearnListHook from '../../components/skills/useLearnList';

// Mock the hook
vi.mock('../../components/skills/useLearnList', () => ({
  useLearnList: vi.fn(),
}));

vi.mock('../../components/skills/EditSkillModal', () => ({
  EditSkillModal: ({ skill, onSave }: any) => {
    // Simple mock that captures input
    let currentName = skill.name || '';
    let currentDesc = skill.description || '';
    return (
      <div>
        <input 
            placeholder="Skill Name"
            defaultValue={skill.name}
            onChange={(e) => currentName = e.target.value}
        />
        <textarea 
          defaultValue={skill.description} 
          onChange={(e) => currentDesc = e.target.value}
        />
        <button onClick={() => onSave({ name: currentName, description: currentDesc, learningPath: skill.learningPath })}>
          {skill.name ? 'Save Changes' : 'Create Skill'}
        </button>
      </div>
    );
  }
}));

describe('SkillsManager', () => {
  const mockReorderSkills = vi.fn();
  const mockRemoveSkill = vi.fn();
  const mockSaveSkill = vi.fn();
  const mockUpdateSkill = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useLearnListHook.useLearnList as any).mockReturnValue({
      learnList: [
        { name: 'React', description: 'Frontend Lib', learningPath: [] },
        { name: 'TypeScript', description: 'Typed JS', learningPath: ['https://ts.dev'] },
        { name: 'Node.js', description: 'Backend', learningPath: [] }
      ],
      reorderSkills: mockReorderSkills,
      removeSkill: mockRemoveSkill,
      updateSkill: mockUpdateSkill,
      saveSkill: mockSaveSkill,
    });
    // Mock window.confirm
    vi.spyOn(window, 'confirm').mockImplementation(() => true);
  });

  it('renders list of skills in a table', () => {
    render(<SkillsManager />);
    expect(screen.getByText('React')).toBeInTheDocument();
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
    expect(screen.getByText('Node.js')).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('renders empty state when list is empty', () => {
    (useLearnListHook.useLearnList as any).mockReturnValue({
      learnList: [],
      reorderSkills: mockReorderSkills,
      removeSkill: mockRemoveSkill,
      saveSkill: mockSaveSkill,
    });
    render(<SkillsManager />);
    expect(screen.getByText(/No skills in your learn list yet/i)).toBeInTheDocument();
  });

  it('toggles between table and markdown view', () => {
    render(<SkillsManager />);
    
    // Initial state: View MD button visible, Table visible
    const toggleButton = screen.getByText('View MD');
    expect(toggleButton).toBeInTheDocument();
    expect(screen.getByRole('table')).toBeInTheDocument();
    
    // Click View MD
    fireEvent.click(toggleButton);
    
    // View Table button visible, Table hidden
    expect(screen.getByText('View Table')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    
    // Check for markdown content (Rendered)
    // "# My Skills" becomes an h1 with text "My Skills"
    expect(screen.getByRole('heading', { level: 1, name: /My Skills/i })).toBeInTheDocument();
    
    // Click View Table
    fireEvent.click(screen.getByText('View Table'));
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('calls reorderSkills when dragging and dropping', () => {
    render(<SkillsManager />);
    const rows = screen.getAllByRole('row');
    // rows[0] is header, rows[1] is React, rows[2] is TypeScript, rows[3] is Node.js
    
    const sourceRow = rows[1]; // React
    const targetRow = rows[2]; // TypeScript
    
    const mockDataTransfer = {
      effectAllowed: '',
      dropEffect: '',
    };
    
    fireEvent.dragStart(sourceRow, {
      dataTransfer: mockDataTransfer
    });
    fireEvent.dragOver(targetRow, {
      dataTransfer: mockDataTransfer
    });
    fireEvent.drop(targetRow, {
      dataTransfer: mockDataTransfer
    });
    
    // React moved to index 1 (swapped with TypeScript, but logic inserts it)
    // Original: ['React', 'TypeScript', 'Node.js']
    // Drag 'React' (index 0) to 'TypeScript' (index 1)
    // Result should depend on implementation. Splice(0, 1), Splice(1, 0, item) -> ['TypeScript', 'React', 'Node.js']
    
    expect(mockReorderSkills).toHaveBeenCalled();
    const calledArg = mockReorderSkills.mock.calls[0][0];
    expect(calledArg).toHaveLength(3);
    expect(calledArg[0]).toHaveProperty('name');
    // We expect reorder to be called, exact order depends on drag logic specificity
  });

  it('calls removeSkill when delete button is clicked and confirmed', () => {
    render(<SkillsManager />);
    const deleteButtons = screen.getAllByTitle('Remove Skill');
    
    fireEvent.click(deleteButtons[0]);
    
    expect(window.confirm).toHaveBeenCalled();
    expect(mockRemoveSkill).toHaveBeenCalledWith('React');
  });

  it('opens modal on edit click and saves changes', () => {
    (useLearnListHook.useLearnList as any).mockReturnValue({
      learnList: [{ name: 'React', description: 'Old Desc', learningPath: [] }],
      reorderSkills: mockReorderSkills,
      removeSkill: mockRemoveSkill,
      saveSkill: mockSaveSkill,
      updateSkill: mockUpdateSkill,
    });

    render(<SkillsManager />);
    
    // Click edit button
    const editButton = screen.getByTitle('Edit Skill');
    fireEvent.click(editButton);
    
    // Verify modal content
    const textarea = screen.getByDisplayValue('Old Desc');
    expect(textarea).toBeInTheDocument();
    
    // Change description
    fireEvent.change(textarea, { target: { value: 'New Desc' } });
    
    // Click Save
    const saveButton = screen.getByText('Save Changes');
    fireEvent.click(saveButton);
    
    expect(mockSaveSkill).toHaveBeenCalledWith(expect.objectContaining({
      name: 'React',
      description: 'New Desc'
    }));
  });

  it('opens modal on add skill click and creates new skill', () => {
    (useLearnListHook.useLearnList as any).mockReturnValue({
      learnList: [],
      reorderSkills: mockReorderSkills,
      removeSkill: mockRemoveSkill,
      saveSkill: mockSaveSkill,
      updateSkill: mockUpdateSkill,
    });

    render(<SkillsManager />);

    // Click Add Skill button
    const addButton = screen.getByText('+ Add Skill');
    fireEvent.click(addButton);

    // Verify modal content - Input for name should be present
    const nameInput = screen.getByPlaceholderText('Skill Name');
    expect(nameInput).toBeInTheDocument();

    // Enter name
    fireEvent.change(nameInput, { target: { value: 'New Skill' } });

    // Click Save (Create Skill)
    const createButton = screen.getByText('Create Skill');
    fireEvent.click(createButton);

    expect(mockSaveSkill).toHaveBeenCalledWith(expect.objectContaining({
      name: 'New Skill',
      description: '',
      learningPath: []
    }));
  });
});
