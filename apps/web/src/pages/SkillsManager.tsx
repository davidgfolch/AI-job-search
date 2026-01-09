import { useState } from 'react';
import { useLearnList, type Skill } from '../components/skills/useLearnList';
import { SkillsTable } from '../components/skills/SkillsTable';
import { EditSkillModal } from '../components/skills/EditSkillModal';
import './SkillsManager.css';

const SkillsManager = () => {
  const { learnList, reorderSkills, removeSkill, updateSkill } = useLearnList();
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);

  const handleRemove = (skill: string) => {
    if (window.confirm(`Remove "${skill}" from learn list?`)) {
      removeSkill(skill);
    }
  };

  const saveEdit = (updates: { description: string; learningPath: string[] }) => {
    if (editingSkill) {
      updateSkill(editingSkill.name, updates);
      setEditingSkill(null);
    }
  };

  return (
    <div className="skills-manager">
      <h2>Skills Manager</h2>
      
      {learnList.length === 0 ? (
        <div className="empty-state">
          <p>No skills in your learn list yet.</p>
        </div>
      ) : (
        <SkillsTable 
          skills={learnList}
          onReorder={reorderSkills}
          onEdit={setEditingSkill}
          onRemove={handleRemove}
        />
      )}

      {editingSkill && (
        <EditSkillModal 
          skill={editingSkill}
          onSave={saveEdit}
          onClose={() => setEditingSkill(null)}
        />
      )}
    </div>
  );
};

export default SkillsManager;
