import { useState } from 'react';
import { useLearnList } from '../components/skills/useLearnList';
import './SkillsManager.css';

const SkillsManager = () => {
  const { learnList, reorderSkills, removeSkill } = useLearnList();
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  const handleDragStart = (e: React.DragEvent<HTMLTableRowElement>, index: number) => {
    setDraggedIndex(index);
    // Required for Firefox
    e.dataTransfer.effectAllowed = 'move';
    // Set transparent image or keep default ghost
  };

  const handleDragOver = (e: React.DragEvent<HTMLTableRowElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent<HTMLTableRowElement>, targetIndex: number) => {
    e.preventDefault();
    
    if (draggedIndex === null || draggedIndex === targetIndex) return;

    const newList = [...learnList];
    const [draggedItem] = newList.splice(draggedIndex, 1);
    newList.splice(targetIndex, 0, draggedItem);
    
    reorderSkills(newList);
    setDraggedIndex(null);
  };

  const handleRemove = (skill: string) => {
    if (window.confirm(`Remove "${skill}" from learn list?`)) {
      removeSkill(skill);
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
        <table className="skills-table">
          <thead>
            <tr>
              <th>Skill</th>
              <th className="actions-cell">Actions</th>
            </tr>
          </thead>
          <tbody>
            {learnList.map((skill, index) => (
              <tr
                key={skill}
                draggable
                onDragStart={(e) => handleDragStart(e, index)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, index)}
                className={`skill-row ${draggedIndex === index ? 'dragging' : ''}`}
              >
                <td>
                  <span className="skill-name">{skill}</span>
                </td>
                <td className="actions-cell">
                  <button 
                    className="delete-btn"
                    onClick={() => handleRemove(skill)}
                    title="Remove"
                  >
                    ×
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default SkillsManager;
