import { describe, it, expect } from 'vitest';
import { generateSkillsMarkdown } from '../skillUtils';
import { type Skill } from '../../components/skills/useLearnList';

describe('skillUtils', () => {
    describe('generateSkillsMarkdown', () => {
        it('should generate "No skills found" when list is empty', () => {
            const markdown = generateSkillsMarkdown([]);
            expect(markdown).toContain('No skills found');
        });

        it('should format a single skill correctly', () => {
            const skills: Skill[] = [{
                name: 'React',
                description: 'A JS library',
                learningPath: [],
                disabled: false
            }];
            const markdown = generateSkillsMarkdown(skills);
            expect(markdown).toContain('# My Skills');
            expect(markdown).toContain('## React');
            expect(markdown).toContain('A JS library');
        });

        it('should format learning paths correctly', () => {
             const skills: Skill[] = [{
                name: 'TypeScript',
                description: 'Typed Superset',
                learningPath: ['https://typescriptlang.org'],
                disabled: false
            }];
            const markdown = generateSkillsMarkdown(skills);
            expect(markdown).toContain('### Learning Path');
            expect(markdown).toContain('- <https://typescriptlang.org>');
        });

        it('should handle missing descriptions', () => {
              const skills: Skill[] = [{
                name: 'Simple',
                description: '',
                learningPath: [],
                disabled: false
            }];
            const markdown = generateSkillsMarkdown(skills);
            expect(markdown).toContain('## Simple');
            expect(markdown).not.toContain('undefined');
        });

        it('should format multiple skills', () => {
             const skills: Skill[] = [
                 { name: 'A', description: 'Desc A', learningPath: [], disabled: false },
                 { name: 'B', description: 'Desc B', learningPath: [], disabled: false }
             ];
             const markdown = generateSkillsMarkdown(skills);
             expect(markdown).toContain('## A');
             expect(markdown).toContain('Desc A');
             expect(markdown).toContain('## B');
             expect(markdown).toContain('Desc B');
        });

        it('should include a Table of Contents', () => {
             const skills: Skill[] = [
                 { name: 'React Native', description: 'Desc', learningPath: [], disabled: false },
                 { name: 'Go Lang', description: 'Desc', learningPath: [], disabled: false }
             ];
             const markdown = generateSkillsMarkdown(skills);
             expect(markdown).toContain('## Table of Contents');
             expect(markdown).toContain('- [React Native](#react-native)');
             expect(markdown).toContain('- [Go Lang](#go-lang)');
        });
    });
});
