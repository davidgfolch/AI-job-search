import { useState } from 'react';
import { useLearnList, type Skill } from '../components/skills/useLearnList';
import { SkillsTable } from '../components/skills/SkillsTable';
import { EditSkillModal } from '../components/skills/EditSkillModal';
import './SkillsManager.css';

const SkillsManager = () => {
  const { learnList, reorderSkills, removeSkill, updateSkill, isLoading, error } = useLearnList();
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Skills Manager</h2>
      </div>
      
      {error && <div className="error-message" style={{ color: 'red', margin: '10px 0' }}>{error}</div>}
      {isLoading && <div className="loading-indicator">Loading skills...</div>}

      {!isLoading && learnList.length === 0 ? (
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
