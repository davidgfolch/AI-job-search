import { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import type { Skill } from './useLearnList';
import { skillsApi } from '../../api/skills';

interface UseEditSkillFormProps {
  skill: Skill;
  onSave: (skill: Skill) => void;
  onUpdate?: (skill: Skill) => void;
}

export const useEditSkillForm = ({ skill, onSave, onUpdate }: UseEditSkillFormProps) => {
  const queryClient = useQueryClient();
  const [name, setName] = useState(skill.name || '');
  const [description, setDescription] = useState(skill.description || '');
  const [learningPath, setLearningPath] = useState<string[]>(skill.learningPath || []);
  const [newLinkInput, setNewLinkInput] = useState('');
  const [isPolling, setIsPolling] = useState(false);
  
  const isNewSkill = !skill.name;

  useEffect(() => {
    setName(skill.name || '');
    setDescription(skill.description || '');
    setLearningPath(skill.learningPath || []);
    setNewLinkInput('');
  }, [skill]);

  const handleSave = () => {
    if (!name.trim()) {
        alert("Skill name is required");
        return;
    }
    onSave({
      name,
      description,
      learningPath,
      disabled: skill.disabled,
      ai_enriched: skill.ai_enriched
    });
  };

  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [name, description, learningPath, skill]); // Dependencies for handleSave closure

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

  const handleAutoFill = async () => {
    if (!name.trim()) return;
    setIsPolling(true);
    // Trigger enrichment, ai_enriched=false (0) forces enrichment
    await onUpdate?.({ 
        ...skill, 
        name,
        description: '', 
        learningPath,
        ai_enriched: false 
    });
    const interval = setInterval(async () => { // Start polling
        try {
            const latest = await skillsApi.getSkill(name);
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
     if (!name.trim()) return;
     await queryClient.invalidateQueries({ queryKey: ['skills'] });
     try {
         const latest = await skillsApi.getSkill(name);
         if (latest) {
             setDescription(latest.description || '');
             setLearningPath(latest.learningPath || []);
         }
     } catch (e) {
         console.error("Failed to refresh individual skill", e);
     }
  };

  const handleLinkInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleAddLink();
  };

  return {
    name,
    setName,
    description,
    setDescription,
    learningPath,
    newLinkInput,
    setNewLinkInput,
    isPolling,
    isNewSkill,
    handleAddLink,
    handleRemoveLink,
    handleSave,
    handleAutoFill,
    handleReload,
    handleLinkInputKeyDown
  };
};
