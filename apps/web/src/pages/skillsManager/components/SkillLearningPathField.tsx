import React from 'react';
import { FormField } from '../../common/components/core/FormField';
import type { LearningPathLink } from '../api/SkillsManagerApi';


interface SkillLearningPathFieldProps {
  learningPath: LearningPathLink[]; // This is the edited state
  skillLearningPath: LearningPathLink[]; // This is the original skill state (safe to access if view mode, but we can pass the relevant list based on view mode)
  isViewMode: boolean;
  newLinkInput: string;
  setNewLinkInput: (val: string) => void;
  handleAddLink: () => void;
  handleRemoveLink: (index: number) => void;
  handleClearAllLinks: () => void;
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
  handleClearAllLinks,
  handleLinkInputKeyDown
}) => {
  return (
    <FormField id="learning-path-input" label="Learning Path" className="form-group">
      {isViewMode ? (
        <div className="links-list">
          {(skillLearningPath && skillLearningPath.length > 0) ? (
            <>
              <div className="links-list-header">
                <button
                  className="btn-icon delete clear-all"
                  onClick={() => {
                    if (window.confirm('Remove all learning path links?')) {
                      handleClearAllLinks();
                    }
                  }}
                  title="Clear all links"
                >
                  Clear all
                </button>
              </div>
              {skillLearningPath.map((link, i) => (
                <div key={i} className="link-item">
                  <span className="link-source" title={`Source: ${link.source}`}>{link.source}</span>
                  <a href={link.url} target="_blank" rel="noopener noreferrer" className="link-url" style={{ textDecoration: 'underline', color: 'var(--primary-color)' }}>
                    {link.url}
                  </a>
                  <button
                    className="btn-icon delete link-remove"
                    onClick={() => handleRemoveLink(i)}
                    title="Remove link"
                  >
                    ×
                  </button>
                </div>
              ))}
            </>
          ) : <div style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No learning path links</div>}
        </div>
      ) : (
        <div className="links-list">
          {learningPath.map((link, i) => (
            <div key={i} className="link-item">
              <span className="link-source" title={`Source: ${link.source}`}>{link.source}</span>
              <span className="link-url">{link.url}</span>
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
              id="learning-path-input"
              name="learning-path"
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
    </FormField>
  );
};
