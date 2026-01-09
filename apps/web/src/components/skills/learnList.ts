const LEARN_LIST_KEY = 'job-skills-learn-list';

/**
 * Get the current learn list from localStorage
 */
export const getLearnList = (): string[] => {
  try {
    const stored = localStorage.getItem(LEARN_LIST_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error('Error loading learn list:', error);
    return [];
  }
};

/**
 * Save the learn list to localStorage
 */
export const updateLearnList = (list: string[]): void => {
  try {
    localStorage.setItem(LEARN_LIST_KEY, JSON.stringify(list));
  } catch (error) {
    console.error('Error saving learn list:', error);
  }
};

const saveLearnList = updateLearnList;

/**
 * Add a skill to the learn list
 */
export const addToLearnList = (skill: string): void => {
  const list = getLearnList();
  const normalizedSkill = skill.trim();
  if (!list.includes(normalizedSkill)) {
    list.push(normalizedSkill);
    saveLearnList(list);
  }
};

/**
 * Remove a skill from the learn list
 */
export const removeFromLearnList = (skill: string): void => {
  const list = getLearnList();
  const normalizedSkill = skill.trim();
  const filtered = list.filter(s => s !== normalizedSkill);
  saveLearnList(filtered);
};

/**
 * Toggle a skill in the learn list (add if not present, remove if present)
 */
export const toggleLearnList = (skill: string): void => {
  const list = getLearnList();
  const normalizedSkill = skill.trim();
  if (list.includes(normalizedSkill)) {
    removeFromLearnList(normalizedSkill);
  } else {
    addToLearnList(normalizedSkill);
  }
};

/**
 * Check if a skill is in the learn list
 */
export const isInLearnList = (skill: string): boolean => {
  const list = getLearnList();
  return list.includes(skill.trim());
};
