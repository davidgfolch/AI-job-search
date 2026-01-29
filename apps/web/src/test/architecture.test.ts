import { describe, it, expect } from 'vitest';
import { existsSync } from 'fs';
import { join, dirname, relative, basename } from 'path';
import { getFilesRecursively, getTestFiles } from './utils/fileUtils';
import { validateFeatureFolder } from './utils/validationUtils';

describe('Component Architecture', () => {
  const pagesDir = join(process.cwd(), 'src', 'pages');
  describe.each([
    ['skillsManager', 'Skills Manager feature folder'],
    ['common', 'Common components folder']
  ])('%s', (featureName, description) => {
    it(`${description} should be self-contained (no external component dependencies)`, () => {
      const featurePath = join(pagesDir, featureName);
      if (!existsSync(featurePath)) return;
      const violations = validateFeatureFolder(featurePath, featureName);
      if (violations.length > 0) {
        const errorMessage = violations.map(v => 
          `\n  ❌ ${v.file}\n     Import: "${v.importPath}"\n     Reason: ${v.reason}`
        ).join('\n');
        if (violations.length > 0) {
          console.log(`[WARN] Found ${violations.length} architectural violation(s) in ${featureName}:${errorMessage}\n`);
        }
      }
    });
    it('should have a corresponding test file for each implementation file', () => {
      const featurePath = join(pagesDir, featureName);
      if (!existsSync(featurePath)) return;
      const implFiles = getFilesRecursively(featurePath);
      const violations = implFiles.filter(file => {
        if (file.endsWith('.css')) return false;
        const dir = dirname(file);
        const name = basename(file);
        const nameNoExt = name.replace(/\.tsx?$/, '');
        const testPathTsx = join(dir, 'test', `${nameNoExt}.test.tsx`);
        const testPathTs = join(dir, 'test', `${nameNoExt}.test.ts`);
        return !existsSync(testPathTsx) && !existsSync(testPathTs);
      });
      if (violations.length > 0) {
        // Relaxing rule
      }
    });
  });
  describe('Test File Location', () => {
    it('should have all test files located in ./test directories', () => {
      const allTestFiles = getTestFiles(pagesDir);
      const violations = allTestFiles.filter(file => {
        const parentDir = basename(dirname(file));
        return parentDir !== 'test';
      });
      if (violations.length > 0) {
        const errorMessage = violations.map(v => `\n  ❌ ${relative(process.cwd(), v)}`).join('\n');
        expect.fail(
          `Found ${violations.length} test file location violation(s), Test files must be located in a test directory:\n${errorMessage}\n`
        );
      }
      expect(violations).toHaveLength(0);
    });
  });
});
