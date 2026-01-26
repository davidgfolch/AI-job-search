import ReactMarkdown from 'react-markdown';
import type { Skill } from './useLearnList';
import { useEditSkillForm } from './useEditSkillForm';

interface EditSkillModalProps {
  skill: Skill;
  onSave: (skill: Skill) => void;
  onUpdate?: (skill: Skill) => void;
  onClose: () => void;
}

declare const __AI_ENRICH_SKILL_ENABLED__: boolean;

export const EditSkillModal = ({ skill, onSave, onUpdate, onClose }: EditSkillModalProps) => {
  const {
    name, setName,
    description, setDescription,
    learningPath,
    newLinkInput, setNewLinkInput,
    isPolling,
    isNewSkill,
    handleAddLink,
    handleRemoveLink,
    handleSave,
    handleAutoFill,
    handleReload,
    handleLinkInputKeyDown
  } = useEditSkillForm({ skill, onSave, onUpdate });

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>{isNewSkill ? 'Add New Skill' : `Edit Skill: ${skill.name}`}</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          {isNewSkill && (
              <div className="form-group">
                  <label>Skill Name</label>
                  <input
                      type="text"
                      className="skill-input"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. React, Python, ..."
                      autoFocus
                  />
              </div>
          )}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ marginBottom: 0 }}>Description</label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {!isNewSkill && (
                    <button
                        className="btn-secondary"
                        style={{ fontSize: '0.8rem', padding: '4px 8px' }}
                        onClick={handleReload}
                        title="Reload all skills"
                    >↻
                    </button>
                  )}
                  {__AI_ENRICH_SKILL_ENABLED__ && (
                    <button 
                        className="btn-secondary" 
                        style={{ fontSize: '0.8rem', padding: '4px 8px' }}
                        onClick={handleAutoFill}
                        disabled={isPolling || !name.trim()}
                    >
                        {isPolling ? 'Generating...' : 'Auto-fill with AI'}
                    </button>
                  )}
                </div>
            </div>
            <div className="description-editor-container">
                <textarea
                  className="skill-textarea"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Add a description... (Markdown supported)"
                  rows={isNewSkill ? 6 : 8}
                  disabled={isPolling}
                />
                <div className="description-preview">
                    {description ? (<ReactMarkdown>{description}</ReactMarkdown>)
                     : (<span style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>Markdown validation</span>)}
                </div>
            </div>
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
          </div>
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave}>{isNewSkill ? 'Create Skill' : 'Save Changes'}</button>
        </div>
      </div>
    </div>
  );
};

