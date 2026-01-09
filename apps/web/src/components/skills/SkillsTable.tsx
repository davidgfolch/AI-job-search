import { useState } from 'react';
import type { Skill } from './useLearnList';

interface SkillsTableProps {
  skills: Skill[];
  onReorder: (skills: Skill[]) => void;
  onEdit: (skill: Skill) => void;
  onRemove: (skillName: string) => void;
}

export const SkillsTable = ({ skills, onReorder, onEdit, onRemove }: SkillsTableProps) => {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  const handleDragStart = (e: React.DragEvent<HTMLTableRowElement>, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    // Small timeout to allow the ghost image to be created before hiding the row
    setTimeout(() => {
        // Optional visual tweak
    }, 0);
  };

  const handleDragOver = (e: React.DragEvent<HTMLTableRowElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent<HTMLTableRowElement>, targetIndex: number) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === targetIndex) return;

    const newList = [...skills];
    const [draggedItem] = newList.splice(draggedIndex, 1);
    newList.splice(targetIndex, 0, draggedItem);
    
    onReorder(newList);
    setDraggedIndex(null);
  };

  return (
    <div className="skills-table-container">
      <table className="skills-table">
        <thead>
          <tr>
            <th className="col-handle"></th>
            <th className="col-skill">Skill</th>
            <th className="col-desc">Description</th>
            <th className="col-links">Learning Path</th>
            <th className="col-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          {skills.map((skill, index) => (
            <tr
              key={skill.name}
              draggable
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, index)}
              className={`skill-row ${draggedIndex === index ? 'dragging' : ''} ${skill.disabled ? 'disabled' : ''}`}
            >
              <td>
                <div className="drag-handle" title="Drag to reorder">⋮⋮</div>
              </td>
              <td>
                <span className="skill-name">{skill.name}</span>
              </td>
              <td>
                <div className="read-only-text">{skill.description}</div>
              </td>
              <td>
                <div className="links-list read-only">
                  {skill.learningPath.map((link, i) => (
                    <a key={i} href={link} target="_blank" rel="noopener noreferrer" className="link-url">
                      {link}
                    </a>
                  ))}
                </div>
              </td>
              <td className="actions-cell">
                <button 
                  className="btn-icon edit"
                  onClick={() => onEdit(skill)}
                  title="Edit Skill"
                >
                  ✎
                </button>
                <button 
                  className="btn-icon delete"
                  onClick={() => onRemove(skill.name)}
                  title="Remove Skill"
                >
                  ×
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
