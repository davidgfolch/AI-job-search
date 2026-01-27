import { type Skill } from '../components/skills/useLearnList';

/**
 * Generates a markdown string from a list of skills.
 * @param skills The list of skills to export.
 * @returns A formatted markdown string.
 */
export const generateSkillsMarkdown = (skills: Skill[]): string => {
  let markdown = '# My Skills\n\n';

  if (!skills || skills.length === 0) {
    return markdown + 'No skills found.\n';
  }

  markdown += '## Table of Contents\n\n';
  skills.forEach((skill) => {
    const slug = skill.name
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-');
    markdown += `- [${skill.name}](#${slug})\n`;
  });
  markdown += '\n';

  skills.forEach((skill) => {
    markdown += `## ${skill.name}\n\n`;
    
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
