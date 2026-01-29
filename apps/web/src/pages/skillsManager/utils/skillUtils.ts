import { type Skill } from '../hooks/useLearnList';

/**
 * Generates a markdown string from a list of skills.
 * @param skills The list of skills to export.
 * @returns A formatted markdown string.
 */
/**
 * Normalizes skill name for comparison (case-insensitive, specific replacements).
 * Matches backend normalization.
 */
export const normalizeName = (name: string): string => {
  // Replace non-alphanumeric chars (except space, +, #, .) with space
  // Maintain consistency with backend
  const cleaned = name.replace(/[^a-zA-Z0-9\s\+\.#]/g, ' ');
  // Collapse multiple spaces and trim, then lowercase
  return cleaned.replace(/\s+/g, ' ').trim().toLowerCase();
};

export const generateSkillsMarkdown = (skills: Skill[]): string => {
  let markdown = '# My Skills\n\n';

  if (!skills || skills.length === 0) {
    return markdown + 'No skills found.\n';
  }

  markdown += '## Table of Contents\n\n';
  
  // Group skills by category
  const categories: Record<string, Skill[]> = {};
  skills.forEach(skill => {
      // Split category by comma if multiple
      const cats = skill.category ? skill.category.split(',').map(c => c.trim()) : ['Other'];
      cats.forEach(cat => {
          if (!categories[cat]) categories[cat] = [];
          categories[cat].push(skill);
      });
  });

  // Sort categories and skills
  const sortedCategories = Object.keys(categories).sort();
  
  sortedCategories.forEach(cat => {
      markdown += `### ${cat}\n`;
      categories[cat].sort((a, b) => a.name.localeCompare(b.name)).forEach(skill => {
        const slug = skill.name
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/\s+/g, '-');
        markdown += `- [${skill.name}](#${slug})\n`;
      });
      markdown += '\n';
  });

  // Full Details
  markdown += '\n---\n\n';

  skills.forEach((skill) => {
    markdown += `## ${skill.name}\n\n`;
    
    if (skill.category) {
        markdown += `**Category**: ${skill.category}\n\n`;
    }

    if (skill.description) {
      markdown += `${skill.description.trim()}\n\n`;
    }

    if (skill.learningPath && skill.learningPath.length > 0) {
      markdown += '### Learning Path\n\n';
      skill.learningPath.forEach((url) => {
        markdown += `- <${url}>\n`;
      });
      markdown += '\n';
    }
  });

  return markdown;
};
