import { useState, useEffect } from 'react';
import { getLearnList, toggleLearnList as toggleLearnListUtil, updateLearnList, type Skill } from './learnList';
export type { Skill };

/**
 * Custom hook to manage the skills learn list
 */
export const useLearnList = () => {
  const [learnList, setLearnList] = useState<Skill[]>([]);

  useEffect(() => {
    setLearnList(getLearnList());
  }, []);

  const toggleSkill = (skill: string) => {
    toggleLearnListUtil(skill);
    setLearnList(getLearnList());
  };

  const isInLearnList = (skill: string): boolean => {
    const s = learnList.find(s => s.name === skill.trim());
    return !!s && !s.disabled;
  };

  const reorderSkills = (newList: Skill[]) => {
    updateLearnList(newList);
    setLearnList(newList);
  };

  const updateSkill = (name: string, updates: Partial<Skill>) => {
    const newList = learnList.map(skill => 
      skill.name === name ? { ...skill, ...updates } : skill
    );
    updateLearnList(newList);
    setLearnList(newList);
  };

  const removeSkill = (skill: string) => {
    toggleSkill(skill);
  };

  return { learnList, toggleSkill, reorderSkills, removeSkill, isInLearnList, updateSkill };
};
