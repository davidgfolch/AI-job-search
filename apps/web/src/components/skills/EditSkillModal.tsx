import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { useQueryClient } from '@tanstack/react-query';
import type { Skill } from './useLearnList';
import { skillsApi } from '../../api/skills';

interface EditSkillModalProps {
  skill: Skill;
  onSave: (updates: { description: string; learningPath: string[] }) => void;
  onUpdate?: (skill: Skill) => void;
  onClose: () => void;
}

declare const __AI_ENRICH_SKILL_ENABLED__: boolean;

export const EditSkillModal = ({ skill, onSave, onUpdate, onClose }: EditSkillModalProps) => {

  const queryClient = useQueryClient();
  const [description, setDescription] = useState(skill.description || '');
  const [learningPath, setLearningPath] = useState<string[]>(skill.learningPath || []);
  const [newLinkInput, setNewLinkInput] = useState('');
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => { // Update state when skill changes
    setDescription(skill.description || '');
    setLearningPath(skill.learningPath || []);
    setNewLinkInput('');
  }, [skill]);

  useEffect(() => { // Handle Ctrl+Enter to save
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

  const handleAutoFill = async () => {
    setIsPolling(true);
    // Trigger enrichment, ai_enriched=false (0) forces enrichment
    await onUpdate?.({ 
        ...skill, 
        description: '', 
        learningPath,
        ai_enriched: false 
    });
    
    const interval = setInterval(async () => { // Start polling
        try {
            const latest = await skillsApi.getSkill(skill.name);
            if (latest && latest.ai_enriched && latest.description) {
                setDescription(latest.description);
                setIsPolling(false);
                clearInterval(interval);
            }
        } catch (e) {
            // ignore error
        }
    }, 2000);
    return () => clearInterval(interval);
  };

  const handleReload = async () => {
     await queryClient.invalidateQueries({ queryKey: ['skills'] });
     try {
         const latest = await skillsApi.getSkill(skill.name);
         if (latest) {
             setDescription(latest.description || '');
             setLearningPath(latest.learningPath || []);
         }
     } catch (e) {
         console.error("Failed to refresh individual skill", e);
     }
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label style={{ marginBottom: 0 }}>Description</label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                      className="btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '4px 8px' }}
                      onClick={handleReload}
                      title="Reload all skills"
                  >↻
                  </button>
                  {__AI_ENRICH_SKILL_ENABLED__ && (
                    <button 
                        className="btn-secondary" 
                        style={{ fontSize: '0.8rem', padding: '4px 8px' }}
                        onClick={handleAutoFill}
                        disabled={isPolling}
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
                  rows={8}
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
