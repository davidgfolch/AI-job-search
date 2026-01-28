import React from 'react';
import type { Skill } from './useLearnList';
import { useEditSkillForm } from './useEditSkillForm';
import { SkillDescriptionField } from './SkillDescriptionField';
import { SkillLearningPathField } from './SkillLearningPathField';

declare const __AI_ENRICH_SKILL_ENABLED__: boolean;

interface EditSkillModalProps {
  skill: Skill;
  onSave: (skill: Skill) => void;
  onUpdate?: (skill: Skill) => void;
  onClose: () => void;
  onNext?: () => void;
  onPrevious?: () => void;
  hasNext?: boolean;
  hasPrevious?: boolean;
}

export const EditSkillModal = ({ skill, onSave, onUpdate, onClose, onNext, onPrevious, hasNext, hasPrevious }: EditSkillModalProps) => {
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
            {!isNewSkill && (
              <button
                className="btn-secondary"
                style={{ padding: '4px 8px', fontSize: '1.2rem', lineHeight: '1rem' }}
                onClick={handleReload}
                title="Reload all skills"
              >
                ↻
              </button>
            )}
            {!isNewSkill && (
              <>
                <button
                  className="btn-secondary"
                  onClick={onPrevious}
                  disabled={!hasPrevious}
                  style={{ padding: '4px 8px', fontSize: '1.2rem', lineHeight: '1rem' }}
                  title="Previous Skill"
                >
                  ⏮
                </button>
                <button
                  className="btn-secondary"
                  onClick={onNext}
                  disabled={!hasNext}
                  style={{ padding: '4px 8px', fontSize: '1.2rem', lineHeight: '1rem' }}
                  title="Next Skill"
                >
                  ⏭
                </button>
              </>
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
                <div style={{ padding: '8px 0', fontSize: '1rem' }}>{category || 'No category'}</div>
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
          />

          <SkillLearningPathField
            learningPath={learningPath}
            skillLearningPath={learningPath}
            isViewMode={isViewMode}
            newLinkInput={newLinkInput}
            setNewLinkInput={setNewLinkInput}
            handleAddLink={handleAddLink}
            handleRemoveLink={handleRemoveLink}
            handleLinkInputKeyDown={handleLinkInputKeyDown}
          />
        </div>
        {!isViewMode && (
          <div className="modal-footer">
            <button className="btn-primary" onClick={handleSave}>{isNewSkill ? 'Create Skill' : 'Save Changes'}</button>
          </div>
        )}
      </div>
    </div>
  );
};


