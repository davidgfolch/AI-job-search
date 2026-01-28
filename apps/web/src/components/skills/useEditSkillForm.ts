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
  const [category, setCategory] = useState(skill.category || '');
  const [description, setDescription] = useState(skill.description || '');
  const [learningPath, setLearningPath] = useState<string[]>(skill.learningPath || []);
  const [newLinkInput, setNewLinkInput] = useState('');
  const [isPolling, setIsPolling] = useState(false);
  
  const isNewSkill = !skill.name;

  useEffect(() => {
    setName(skill.name || '');
    setCategory(skill.category || '');
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
      category,
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
  }, [name, category, description, learningPath, skill]); // Dependencies for handleSave closure

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

  useEffect(() => {
    if (!isPolling || !name.trim()) return;
    const interval = setInterval(async () => {
      try {
        const latest = await skillsApi.getSkill(name);
        if (latest && latest.ai_enriched && latest.description) {
          setDescription(latest.description);
          if (latest.category) setCategory(latest.category);
          if (latest.learningPath && latest.learningPath.length > 0) {
              setLearningPath(latest.learningPath);
          }
          setIsPolling(false);
          await queryClient.invalidateQueries({ queryKey: ['skills'] });
        }
      } catch (e) {
        console.error("Polling error:", e);
      }
    }, 10000);
    return () => clearInterval(interval);
  }, [isPolling, name, queryClient]);

  const handleAutoFill = async () => {
    if (!name.trim()) return;
    setIsPolling(true);
    await onUpdate?.({ 
        ...skill, 
        name,
        description: '', 
        learningPath,
        ai_enriched: false 
    });
  };

  const handleReload = async () => {
     if (!name.trim()) return;
     await queryClient.invalidateQueries({ queryKey: ['skills'] });
     try {
         const latest = await skillsApi.getSkill(name);
         if (latest) {
             setDescription(latest.description || '');
             setCategory(latest.category || '');
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
    category,
    setCategory,
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
