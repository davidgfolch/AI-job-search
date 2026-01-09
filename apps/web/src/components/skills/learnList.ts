const LEARN_LIST_KEY = 'job-skills-learn-list';

/**
 * Get the current learn list from localStorage
 */
export interface Skill {
  name: string;
  description: string;
  learningPath: string[];
  disabled?: boolean;
}

/**
 * Get the current learn list from localStorage
 */
export const getLearnList = (): Skill[] => {
  try {
    const stored = localStorage.getItem(LEARN_LIST_KEY);
    if (!stored) return [];

    const parsed = JSON.parse(stored);
    
    // Migration: if array of strings, convert to objects
    if (Array.isArray(parsed) && parsed.length > 0 && typeof parsed[0] === 'string') {
      const migrated: Skill[] = (parsed as unknown as string[]).map(name => ({
        name,
        description: '',
        learningPath: [],
        disabled: false
      }));
      // Save migrated data back immediately
      updateLearnList(migrated);
      return migrated;
    }

    return parsed as Skill[];
  } catch (error) {
    console.error('Error loading learn list:', error);
    return [];
  }
};

/**
 * Save the learn list to localStorage
 */
export const updateLearnList = (list: Skill[]): void => {
  try {
    localStorage.setItem(LEARN_LIST_KEY, JSON.stringify(list));
  } catch (error) {
    console.error('Error saving learn list:', error);
  }
};



/**
 * Add a skill to the learn list
 */
/**
 * Add a skill to the learn list
 */
export const addToLearnList = (skillName: string): void => {
  const list = getLearnList();
  const normalizedSkill = skillName.trim();
  const existingIndex = list.findIndex(s => s.name === normalizedSkill);

  if (existingIndex >= 0) {
    // If exists but disabled, re-enable it
    if (list[existingIndex].disabled) {
      list[existingIndex].disabled = false;
      updateLearnList(list);
    }
  } else {
    // Add new
    list.push({
      name: normalizedSkill,
      description: '',
      learningPath: [],
      disabled: false
    });
    updateLearnList(list);
  }
};

/**
 * Remove a skill from the learn list.
 * If the skill has description or learning path, it is marked as disabled (soft delete).
 * Otherwise it is removed completely.
 */
export const removeFromLearnList = (skillName: string): void => {
  const list = getLearnList();
  const normalizedSkill = skillName.trim();
  const index = list.findIndex(s => s.name === normalizedSkill);

  if (index === -1) return;

  const skill = list[index];
  const hasContent = (skill.description && skill.description.trim().length > 0) || 
                     (skill.learningPath && skill.learningPath.length > 0);

  if (hasContent) {
    // Soft delete
    skill.disabled = true;
    updateLearnList(list);
  } else {
    // Hard delete
    list.splice(index, 1);
    updateLearnList(list);
  }
};

/**
 * Toggle a skill in the learn list (add if not present/disabled, remove if present & enabled)
 */
export const toggleLearnList = (skillName: string): void => {
  if (isInLearnList(skillName)) {
    removeFromLearnList(skillName);
  } else {
    addToLearnList(skillName);
  }
};

/**
 * Check if a skill is in the learn list
 */
export const isInLearnList = (skillName: string): boolean => {
  const list = getLearnList();
  const normalized = skillName.trim();
  const skill = list.find(s => s.name === normalized);
  return !!skill && !skill.disabled;
};
