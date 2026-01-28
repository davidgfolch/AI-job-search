import React from 'react';


interface SkillLearningPathFieldProps {
  learningPath: string[]; // This is the edited state
  skillLearningPath: string[]; // This is the original skill state (safe to access if view mode, but we can pass the relevant list based on view mode)
  isViewMode: boolean;
  newLinkInput: string;
  setNewLinkInput: (val: string) => void;
  handleAddLink: () => void;
  handleRemoveLink: (index: number) => void;
  handleLinkInputKeyDown: (e: React.KeyboardEvent) => void;
}

export const SkillLearningPathField: React.FC<SkillLearningPathFieldProps> = ({
  learningPath,
  skillLearningPath,
  isViewMode,
  newLinkInput,
  setNewLinkInput,
  handleAddLink,
  handleRemoveLink,
  handleLinkInputKeyDown
}) => {
  return (
    <div className="form-group">
      <label>Learning Path</label>
      {isViewMode ? (
        <div className="links-list">
          {(skillLearningPath && skillLearningPath.length > 0) ? skillLearningPath.map((link, i) => (
            <div key={i} className="link-item" style={{ justifyContent: 'flex-start' }}>
              <a href={link} target="_blank" rel="noopener noreferrer" className="link-url" style={{ textDecoration: 'underline', color: 'var(--primary-color)' }}>
                {link}
              </a>
            </div>
          )) : <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No learning path links</div>}
        </div>
      ) : (
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
              onKeyDown={handleLinkInputKeyDown}
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
      )}
    </div>
  );
};
