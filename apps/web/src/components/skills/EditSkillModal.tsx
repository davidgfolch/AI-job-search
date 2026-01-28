import React from 'react';
import type { Skill } from './useLearnList';
import { useEditSkillForm } from './useEditSkillForm';
import { SkillDescriptionField } from './SkillDescriptionField';
import { SkillLearningPathField } from './SkillLearningPathField';

interface EditSkillModalProps {
  skill: Skill;
  onSave: (skill: Skill) => void;
  onUpdate?: (skill: Skill) => void;
  onClose: () => void;
}

export const EditSkillModal = ({ skill, onSave, onUpdate, onClose }: EditSkillModalProps) => {
  const {
    name, setName,
    category, setCategory,
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

  const [isViewMode, setIsViewMode] = React.useState(!isNewSkill);
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <div className="modal-overlay">
      <div className={`modal-content ${isExpanded ? 'expanded' : ''}`}>
        <div className="modal-header">
          <h3>
            {isNewSkill 
              ? 'Add New Skill' 
              : isViewMode 
                ? `Skill: ${skill.name}` 
                : `Edit Skill: ${skill.name}`
            }
          </h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
                className="btn-secondary"
                onClick={() => setIsExpanded(!isExpanded)}
                style={{ padding: '4px 8px', fontSize: '1.2rem', lineHeight: '1rem' }}
                title={isExpanded ? "Collapse" : "Expand"}
            >
                {isExpanded ? '↙' : '↗'}
            </button>
            {!isNewSkill && (
                <button 
                    className="btn-secondary" 
                    onClick={() => setIsViewMode(!isViewMode)}
                    style={{ padding: '4px 8px', fontSize: '0.9rem' }}
                >
                    {isViewMode ? 'Edit' : 'View'}
                </button>
            )}
            <button className="close-btn" onClick={onClose}>×</button>
          </div>
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
            <label>Category</label>
            {isViewMode ? (
                <div style={{ padding: '8px 0', fontSize: '1rem' }}>{skill.category || 'No category'}</div>
            ) : (
                <input
                    type="text"
                    className="skill-input"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    placeholder="e.g. Frameworks, Languages, Tools..."
                />
            )}
          </div>

          <SkillDescriptionField
             description={description}
             setDescription={setDescription}
             isViewMode={isViewMode}
             isNewSkill={isNewSkill}
             isPolling={isPolling}
             skill={skill}
             name={name}
             onReload={handleReload}
             onAutoFill={handleAutoFill}
          />

          <SkillLearningPathField
            learningPath={learningPath}
            skillLearningPath={skill.learningPath || []}
            isViewMode={isViewMode}
            newLinkInput={newLinkInput}
            setNewLinkInput={setNewLinkInput}
            handleAddLink={handleAddLink}
            handleRemoveLink={handleRemoveLink}
            handleLinkInputKeyDown={handleLinkInputKeyDown}
          />
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>{isViewMode ? 'Close' : 'Cancel'}</button>
          {!isViewMode && (
            <button className="btn-primary" onClick={handleSave}>{isNewSkill ? 'Create Skill' : 'Save Changes'}</button>
          )}
        </div>
      </div>
    </div>
  );
};


