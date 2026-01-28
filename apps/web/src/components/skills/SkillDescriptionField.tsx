import React from 'react';
import ReactMarkdown from 'react-markdown';
import type { Skill } from './useLearnList';

interface SkillDescriptionFieldProps {
  description: string;
  setDescription: (value: string) => void;
  isViewMode: boolean;
  isNewSkill: boolean;
  isPolling: boolean;
  skill: Skill;
  name: string;
  onReload: () => void;
  onAutoFill: () => void;
}

declare const __AI_ENRICH_SKILL_ENABLED__: boolean;

export const SkillDescriptionField: React.FC<SkillDescriptionFieldProps> = ({
  description,
  setDescription,
  isViewMode,
  isNewSkill,
  isPolling,
  skill,
  name,
  onReload,
  onAutoFill
}) => {
  return (
    <div className="form-group flex-grow">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <label style={{ marginBottom: 0 }}>Description</label>
        {!isViewMode && (
          <div style={{ display: 'flex', gap: '8px' }}>
            {!isNewSkill && (
              <button
                className="btn-secondary"
                style={{ fontSize: '0.8rem', padding: '4px 8px' }}
                onClick={onReload}
                title="Reload all skills"
              >↻
              </button>
            )}
            {__AI_ENRICH_SKILL_ENABLED__ && (
              <button
                className="btn-secondary"
                style={{ fontSize: '0.8rem', padding: '4px 8px' }}
                onClick={onAutoFill}
                disabled={isPolling || !name.trim()}
              >
                {isPolling ? 'Generating...' : 'Auto-fill with AI'}
              </button>
            )}
          </div>
        )}
      </div>
      {isViewMode ? (
        <div className="description-preview" style={{ height: '100%', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '8px', backgroundColor: 'var(--bg-secondary)', overflowY: 'auto' }}>
          {skill.description ? <ReactMarkdown>{skill.description}</ReactMarkdown> : <span style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No description</span>}
        </div>
      ) : (
        <div className="description-editor-container">
          <textarea
            className="skill-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add a description... (Markdown supported)"
            disabled={isPolling}
          />
          <div className="description-preview">
            {description ? (<ReactMarkdown>{description}</ReactMarkdown>)
              : (<span style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>Markdown validation</span>)}
          </div>
        </div>
      )}
    </div>
  );
};
