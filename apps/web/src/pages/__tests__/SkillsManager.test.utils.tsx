import { vi } from 'vitest';
import { type Skill } from '../../components/skills/useLearnList';

export const mockReorderSkills = vi.fn();
export const mockRemoveSkill = vi.fn();
export const mockSaveSkill = vi.fn();
export const mockUpdateSkill = vi.fn();

export const initialSkills: Skill[] = [
  { name: 'React', description: 'Frontend Lib', learningPath: [], disabled: false },
  { name: 'TypeScript', description: 'Typed JS', learningPath: ['https://ts.dev'], disabled: false },
  { name: 'Node.js', description: 'Backend', learningPath: [], disabled: false }
];

export const setupLearnListMock = (hookModule: any, skills: Skill[] = initialSkills) => {
    hookModule.useLearnList.mockReturnValue({
      learnList: skills,
      reorderSkills: mockReorderSkills,
      removeSkill: mockRemoveSkill,
      updateSkill: mockUpdateSkill,
      saveSkill: mockSaveSkill,
    });
};

export const MockEditSkillModal = ({ skill, onSave }: any) => {
    let currentName = skill.name || '';
    let currentDesc = skill.description || '';
    return (
      <div data-testid="edit-skill-modal">
        <input 
            placeholder="Skill Name"
            defaultValue={skill.name}
            onChange={(e) => currentName = e.target.value}
        />
        <textarea 
          defaultValue={skill.description} 
          onChange={(e) => currentDesc = e.target.value}
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
