import { useState, useEffect } from 'react';
import type { Skill } from './useLearnList';

interface EditSkillModalProps {
  skill: Skill;
  onSave: (updates: { description: string; learningPath: string[] }) => void;
  onClose: () => void;
}

export const EditSkillModal = ({ skill, onSave, onClose }: EditSkillModalProps) => {
  const [description, setDescription] = useState(skill.description || '');
  const [learningPath, setLearningPath] = useState<string[]>(skill.learningPath || []);
  const [newLinkInput, setNewLinkInput] = useState('');

  // Update state when skill changes
  useEffect(() => {
    setDescription(skill.description || '');
    setLearningPath(skill.learningPath || []);
    setNewLinkInput('');
  }, [skill]);

  // Handle Ctrl+Enter to save
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleSave();
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [description, learningPath]); // Add dependencies needed for handleSave closure

  const handleAddLink = () => {
    if (newLinkInput.trim()) {
      setLearningPath([...learningPath, newLinkInput.trim()]);
      setNewLinkInput('');
    }
  };

  const handleRemoveLink = (index: number) => {
    const newPath = [...learningPath];
    newPath.splice(index, 1);
    setLearningPath(newPath);
  };

  const handleSave = () => {
    onSave({
      description,
      learningPath,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddLink();
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Edit Skill: {skill.name}</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <div className="form-group">
            <label>Description</label>
            <textarea
              className="skill-textarea"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add a description..."
              rows={4}
            />
          </div>
          <div className="form-group">
            <label>Learning Path</label>
            <div className="links-list">
              {learningPath.map((link, i) => (
                <div key={i} className="link-item">
                  <span className="link-url">{link}</span>
                  <button 
                    className="btn-icon delete"
                    onClick={() => handleRemoveLink(i)}
                    title="Remove link"
                  >
                    ×
                  </button>
                </div>
              ))}
              <div className="link-input-group">
                <input
                  type="url"
                  className="skill-input"
                  placeholder="Add URL (https://...)"
                  value={newLinkInput}
                  onChange={(e) => setNewLinkInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <button 
                  className="btn-icon add"
                  onClick={handleAddLink}
                  disabled={!newLinkInput}
                  title="Add link"
                >
                  +
                </button>
              </div>
            </div>
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave}>Save Changes</button>
        </div>
      </div>
    </div>
  );
};
