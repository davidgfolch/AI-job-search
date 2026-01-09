import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SkillsManager from '../SkillsManager';
import * as useLearnListHook from '../../components/skills/useLearnList';

// Mock the hook
vi.mock('../../components/skills/useLearnList', () => ({
  useLearnList: vi.fn(),
}));

describe('SkillsManager', () => {
  const mockReorderSkills = vi.fn();
  const mockRemoveSkill = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useLearnListHook.useLearnList as any).mockReturnValue({
      learnList: ['React', 'TypeScript', 'Node.js'],
      reorderSkills: mockReorderSkills,
      removeSkill: mockRemoveSkill,
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
    });
    render(<SkillsManager />);
    expect(screen.getByText(/No skills in your learn list yet/i)).toBeInTheDocument();
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
    // We expect reorder to be called, exact order depends on drag logic specificity
  });

  it('calls removeSkill when delete button is clicked and confirmed', () => {
    render(<SkillsManager />);
    const deleteButtons = screen.getAllByTitle('Remove');
    
    fireEvent.click(deleteButtons[0]);
    
    expect(window.confirm).toHaveBeenCalled();
    expect(mockRemoveSkill).toHaveBeenCalledWith('React');
  });
});
