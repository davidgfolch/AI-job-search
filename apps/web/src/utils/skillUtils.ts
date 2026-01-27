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
