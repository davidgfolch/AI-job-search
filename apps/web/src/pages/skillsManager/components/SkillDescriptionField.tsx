import React from 'react';
import ReactMarkdown from 'react-markdown';
import { FormField } from '../../common/components/core/FormField';

interface SkillDescriptionFieldProps {
  description: string;
  setDescription: (value: string) => void;
  isViewMode: boolean;
}

export const SkillDescriptionField: React.FC<SkillDescriptionFieldProps> = ({
  description,
  setDescription,
  isViewMode
}) => {
  return (
    <FormField id="skill-description-textarea" label="Description" className="form-group flex-grow">
      {isViewMode ? (
        <div className="description-preview" style={{ height: '100%', border: '1px solid var(--border-color)', borderRadius: '4px', padding: '8px', backgroundColor: 'var(--bg-secondary)', overflowY: 'auto' }}>
          {description ? <ReactMarkdown>{description}</ReactMarkdown> : <span style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>No description</span>}
        </div>
      ) : (
        <div className="description-editor-container">
          <textarea
            id="skill-description-textarea"
            name="skill-description"
            className="skill-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Add a description... (Markdown supported)"
          />
          <div className="description-preview">
            {description ? (<ReactMarkdown>{description}</ReactMarkdown>)
              : (<span style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>Markdown validation</span>)}
          </div>
        </div>
      )}
    </FormField>
  );
};
