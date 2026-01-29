import { useState } from 'react';
import { useLearnList, type Skill } from './hooks/useLearnList';
import { SkillsTable } from './components/SkillsTable';
import { EditSkillModal } from './components/EditSkillModal';
import { generateSkillsMarkdown } from './utils/skillUtils';
import { downloadFile } from '../common/utils/fileUtils';
import ReactMarkdownCustom from '../common/components/core/ReactMarkdownCustom';
import './SkillsManager.css';

const SkillsManager = () => {
  const { learnList, reorderSkills, removeSkill, saveSkill, updateSkill, isLoading, error } = useLearnList();
  const [editingSkill, setEditingSkill] = useState<Skill | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'markdown'>('table');

  const handleRemove = (skill: string) => {
    if (window.confirm(`Remove "${skill}" from learn list?`)) {
      removeSkill(skill);
    }
  };

  const saveEdit = (skill: Skill) => {
      saveSkill(skill);
      setEditingSkill(null);
  };

  const handleAddSkill = () => {
      setEditingSkill({
          name: '',
          description: '',
          learningPath: [],
      });
  };

  const handleExport = () => {
    const markdown = generateSkillsMarkdown(learnList);
    downloadFile(markdown, 'my-skills.md', 'text/markdown');
  };

  return (
    <div className="skills-manager">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Skills Manager</h2>
        <div className="actions-group">
          <button 
            className="btn-secondary" 
            onClick={handleExport} 
            disabled={!learnList.length}
            title="Export to Markdown"
          >
              Export
          </button>
          <button 
              className="btn-secondary"
              onClick={() => setViewMode(prev => prev === 'table' ? 'markdown' : 'table')}
              disabled={!learnList.length}
              title={viewMode === 'table' ? "Show Markdown" : "Show Table"}
          >
              {viewMode === 'table' ? 'View MD' : 'View Table'}
          </button>
          <button className="btn-primary" onClick={handleAddSkill}>
              + Add Skill
          </button>
        </div>
      </div>
      
      {error && <div className="error-message" style={{ color: 'red', margin: '10px 0' }}>{error}</div>}
      {isLoading && <div className="loading-indicator">Loading skills...</div>}

      {!isLoading && learnList.length === 0 ? (
        <div className="empty-state">
          <p>No skills in your learn list yet.</p>
        </div>
      ) : (
        viewMode === 'table' ? (
          <SkillsTable 
            skills={learnList}
            onReorder={reorderSkills}
            onEdit={setEditingSkill}
            onRemove={handleRemove}
          />
        ) : (
          <div className="markdown-view">
            <ReactMarkdownCustom>{generateSkillsMarkdown(learnList)}</ReactMarkdownCustom>
          </div>
        )
      )}

      {editingSkill && (
        <EditSkillModal 
          skill={editingSkill}
          onSave={saveEdit}
          onUpdate={(skill) => updateSkill(skill.name, skill)} // Used for autofill updates
          onClose={() => setEditingSkill(null)}
        />
      )}
    </div>
  );
};

export default SkillsManager;
