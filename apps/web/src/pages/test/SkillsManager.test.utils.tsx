import { useState } from 'react';
import { vi } from 'vitest';
import { type Skill, type useLearnList } from '../skillsManager/hooks/useLearnList';

export const mockReorderSkills = vi.fn();
export const mockRemoveSkill = vi.fn();
export const mockSaveSkill = vi.fn();
export const mockUpdateSkill = vi.fn();

export const initialSkills: Skill[] = [
  { name: 'React', description: 'Frontend Lib', learningPath: [], disabled: false },
  { name: 'TypeScript', description: 'Typed JS', learningPath: [{ url: 'https://ts.dev', source: 'llm' }], disabled: false },
  { name: 'Node.js', description: 'Backend', learningPath: [], disabled: false }
];

export const setupLearnListMock = (hookModule: typeof import('../skillsManager/hooks/useLearnList'), skills: Skill[] = initialSkills) => {
    vi.mocked(hookModule.useLearnList).mockReturnValue({
      learnList: skills,
      reorderSkills: mockReorderSkills,
      removeSkill: mockRemoveSkill,
      updateSkill: mockUpdateSkill,
      saveSkill: mockSaveSkill,
    } as unknown as ReturnType<typeof useLearnList>);
};

export const MockEditSkillModal = ({ skill, onSave }: { skill: Skill; onSave: (skill: Skill) => void }) => {
    const [currentName, setCurrentName] = useState(skill.name || '');
    const [currentDesc, setCurrentDesc] = useState(skill.description || '');
    return (
      <div data-testid="edit-skill-modal">
        <input 
            placeholder="Skill Name"
            defaultValue={skill.name}
            onChange={(e) => setCurrentName(e.target.value)}
        />
        <textarea 
          defaultValue={skill.description} 
          onChange={(e) => setCurrentDesc(e.target.value)}
        />
        <button onClick={() => onSave({ 
            name: currentName, 
            description: currentDesc, 
            learningPath: skill.learningPath 
        })}>
          {skill.name ? 'Save Changes' : 'Create Skill'}
        </button>
      </div>
    );
};
