import { useState, useEffect } from 'react';
import { getLearnList, toggleLearnList as toggleLearnListUtil, updateLearnList } from './learnList';

/**
 * Custom hook to manage the skills learn list
 */
export const useLearnList = () => {
  const [learnList, setLearnList] = useState<string[]>([]);

  useEffect(() => {
    setLearnList(getLearnList());
  }, []);

  const toggleSkill = (skill: string) => {
    toggleLearnListUtil(skill);
    setLearnList(getLearnList());
  };

  const isInLearnList = (skill: string): boolean => {
    return learnList.includes(skill.trim());
  };

  const reorderSkills = (newList: string[]) => {
    updateLearnList(newList);
    setLearnList(newList);
  };

  const removeSkill = (skill: string) => {
    toggleSkill(skill);
  };

  return { learnList, toggleSkill, reorderSkills, removeSkill, isInLearnList };
};
