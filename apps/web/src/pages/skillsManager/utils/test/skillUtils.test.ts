import { describe, it, expect } from 'vitest';
import { normalizeName, generateSkillsMarkdown } from '../skillUtils';
import type { Skill } from '../../hooks/useLearnList';

describe('skillUtils', () => {
  describe('normalizeName', () => {
    const testCases = [
      { input: 'React.js', expected: 'react.js' },
      { input: 'C++', expected: 'c++' },
      { input: 'C#', expected: 'c#' },
      { input: 'Node.js  Framework', expected: 'node.js framework' },
      { input: 'Type-Script', expected: 'type script' },
      { input: '  Multiple   Spaces  ', expected: 'multiple spaces' },
    ];

    it.each(testCases)('normalizes "$input" to "$expected"', ({ input, expected }) => {
      expect(normalizeName(input)).toBe(expected);
    });

    it('removes special characters except space, +, #, and .', () => {
      expect(normalizeName('Test@Skill!Name')).toBe('test skill name');
    });

    it('converts to lowercase', () => {
      expect(normalizeName('UPPERCASE')).toBe('uppercase');
    });
  });

  describe('generateSkillsMarkdown', () => {
    it('returns message for empty skills array', () => {
      const result = generateSkillsMarkdown([]);
      expect(result).toContain('# My Skills');
      expect(result).toContain('No skills found.');
    });

    it('generates markdown for single skill', () => {
      const skills: Skill[] = [{
        name: 'JavaScript',
        category: 'Programming',
        description: 'A scripting language',
        learningPath: ['https://example.com'],
      }];
      const result = generateSkillsMarkdown(skills);
      expect(result).toContain('# My Skills');
      expect(result).toContain('## JavaScript');
      expect(result).toContain('**Category**: Programming');
      expect(result).toContain('A scripting language');
      expect(result).toContain('<https://example.com>');
    });

    it('groups skills by category', () => {
      const skills: Skill[] = [
        { name: 'JavaScript', category: 'Programming', description: '', learningPath: [] },
        { name: 'React', category: 'Programming', description: '', learningPath: [] },
        { name: 'Docker', category: 'DevOps', description: '', learningPath: [] },
      ];
      const result = generateSkillsMarkdown(skills);
      expect(result).toContain('### Programming');
      expect(result).toContain('### DevOps');
    });

    it('handles skills with multiple categories', () => {
      const skills: Skill[] = [{
        name: 'Python',
        category: 'Programming, Data Science',
        description: '',
        learningPath: []
      }];
      const result = generateSkillsMarkdown(skills);
      expect(result).toContain('### Data Science');
      expect(result).toContain('### Programming');
    });

    it('sorts categories and skills alphabetically', () => {
      const skills: Skill[] = [
        { name: 'Zebra', category: 'Z Category', description: '', learningPath: [] },
        { name: 'Apple', category: 'A Category', description: '', learningPath: [] },
      ];
      const result = generateSkillsMarkdown(skills);
      const zIndex = result.indexOf('### Z Category');
      const aIndex = result.indexOf('### A Category');
      expect(aIndex).toBeLessThan(zIndex);
    });

    it('handles skills without category', () => {
      const skills: Skill[] = [{ name: 'Uncategorized Skill', description: '', learningPath: [] }];
      const result = generateSkillsMarkdown(skills);
      expect(result).toContain('### Other');
    });
  });
});
