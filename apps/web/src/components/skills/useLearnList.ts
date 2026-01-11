import { useState, useEffect, useCallback } from 'react';
import { skillsApi, type Skill } from '../../api/skills';

export type { Skill };

/**
 * Custom hook to manage the skills learn list
 */
export const useLearnList = () => {
  const [learnList, setLearnList] = useState<Skill[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSkills = useCallback(async () => {
    setIsLoading(true);
    try {
      const skills = await skillsApi.getSkills();
      setLearnList(skills);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch skills", err);
      setError("Failed to load skills from database");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const toggleSkill = async (skillName: string) => {
    const existing = learnList.find(s => s.name === skillName.trim());
    if (existing && !existing.disabled) {
        // Remove (soft delete)
        await removeSkill(skillName);
    } else if (existing && existing.disabled) {
        // Re-enable
        await updateSkill(skillName, { disabled: false });
    } else {
        // Create
        try {
            await skillsApi.createSkill({
                name: skillName.trim(),
                description: '',
                learningPath: [],
                disabled: false
            });
            await fetchSkills();
        } catch (err) {
            console.error("Failed to create skill", err);
        }
    }
  };

  const isInLearnList = (skill: string): boolean => {
    const s = learnList.find(s => s.name === skill.trim());
    return !!s && !s.disabled;
  };

  const reorderSkills = async (newList: Skill[]) => {
    // DB doesn't support reordering easily without an 'order' field. 
    // For now, we update local state but warn or just ignore persistence of order if DB doesnt have it.
    // Actually our DB schema has no order field.
    // So this might just update the view but re-fetch will reset order by name.
    setLearnList(newList);
    // Doing nothing for persistence as DB sorts by name usually or we need an index.
    console.warn("Reordering not fully supported in Database mode yet.");
  };

  const updateSkill = async (name: string, updates: Partial<Skill>) => {
    try {
        await skillsApi.updateSkill(name, updates);
        await fetchSkills();
    } catch (err) {
        console.error("Failed to update skill", err);
    }
  };

  const removeSkill = async (skillName: string) => {
     // Check content for soft delete logic logic?
     // The util does soft delete if description/path exists.
     // We should replicate that logic or move it to API/Backend.
     // API delete is hard delete. Update is soft.
     const skill = learnList.find(s => s.name === skillName.trim());
      if (!skill) return;

      const hasContent = (skill.description && skill.description.trim().length > 0) || 
                        (skill.learningPath && skill.learningPath.length > 0);

      if (hasContent) {
         await updateSkill(skillName, { disabled: true });
      } else {
         try {
             await skillsApi.deleteSkill(skillName);
             await fetchSkills();
         } catch (err) {
             console.error("Failed to delete skill", err);
         }
      }
  };

  return { learnList, toggleSkill, reorderSkills, removeSkill, isInLearnList, updateSkill, isLoading, error, fetchSkills };
};
