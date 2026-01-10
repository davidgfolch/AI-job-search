import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync, statSync, existsSync } from 'fs';
import { join, relative, dirname, resolve, normalize, basename } from 'path';

interface ImportViolation {
  file: string;
  importPath: string;
  reason: string;
}

/**
 * Extract import statements from TypeScript/TSX files
 */
function extractImports(content: string): string[] {
  const imports: string[] = [];
  const importRegex = /import\s+(?:[\w\s{},*]*\s+from\s+)?['"](.*?)['"]/g;
  let match;
  while ((match = importRegex.exec(content)) !== null) {
    imports.push(match[1]);
  }
  return imports;
}

/**
 * Get all TypeScript/TSX files in a directory recursively
 */
function getFilesRecursively(dir: string, fileList: string[] = []): string[] {
  const files = readdirSync(dir);
  files.forEach(file => {
    const filePath = join(dir, file);
    if (statSync(filePath).isDirectory()) {
      if (file !== 'node_modules' && file !== '__tests__' && file !== 'dist' && file !== 'build') {
        getFilesRecursively(filePath, fileList);
      }
    } else if (file.endsWith('.ts') || file.endsWith('.tsx')) {
      if (!file.endsWith('.test.ts') && !file.endsWith('.test.tsx')) {
        fileList.push(filePath);
      }
    }
  });
  return fileList;
}

/**
 * Get all test files in a directory recursively
 */
function getTestFiles(dir: string, fileList: string[] = []): string[] {
  const files = readdirSync(dir);
  files.forEach(file => {
    const filePath = join(dir, file);
    if (statSync(filePath).isDirectory()) {
      if (file !== 'node_modules' && file !== 'dist' && file !== 'build') {
        getTestFiles(filePath, fileList);
      }
    } else if (file.endsWith('.test.ts') || file.endsWith('.test.tsx')) {
      fileList.push(filePath);
    }
  });
  return fileList;
}

/**
 * Check if an import violates feature folder self-containment rules
 */
function checkImportViolation(importPath: string, featureName: string, currentFilePath: string, featureFolderPath: string): string | null {
  // Skip non-relative imports (external libraries, absolute imports)
  if (!importPath.startsWith('.')) {
    return null;
  }

  // Resolve the import path relative to the current file
  const currentDir = dirname(currentFilePath);
  const resolvedPath = normalize(resolve(currentDir, importPath));
  const normalizedFeaturePath = normalize(featureFolderPath);
  
  // Check if the resolved path is outside the feature folder
  if (!resolvedPath.startsWith(normalizedFeaturePath)) {
    // The import escapes the feature folder
    // Determine what kind of external dependency this is
    if (resolvedPath.includes('\\hooks\\') || resolvedPath.includes('/hooks/')) {
      return 'Imports from sibling hooks directory. Use internal hooks instead.';
    }
    if (resolvedPath.includes('\\utils\\') || resolvedPath.includes('/utils/')) {
      return 'Imports from sibling utils directory. Use internal utils instead.';
    }
    // Check for imports from other feature folders
    const featureFolders = ['skills', 'salaryCalculator', 'configurations', 'core'];
    const otherFeatures = featureFolders.filter(f => f !== featureName);
    for (const otherFeature of otherFeatures) {
      if (resolvedPath.includes(`\\components\\${otherFeature}\\`) || resolvedPath.includes(`/components/${otherFeature}/`)) {
        return `Imports from other feature folder (${otherFeature}). Features should be self-contained.`;
      }
    }
  }

  return null;
}

/**
 * Validate that a feature folder doesn't have forbidden dependencies
 */
function validateFeatureFolder(featurePath: string, featureName: string): ImportViolation[] {
  const violations: ImportViolation[] = [];
  const files = getFilesRecursively(featurePath);
  files.forEach(filePath => {
    const content = readFileSync(filePath, 'utf-8');
    const imports = extractImports(content);
    imports.forEach(importPath => {
      const violation = checkImportViolation(importPath, featureName, filePath, featurePath);
      if (violation) {
        const relPath = relative(process.cwd(), filePath);
        violations.push({
          file: relPath,
          importPath,
          reason: violation
        });
      }
    });
  });
  return violations;
}

describe('Component Architecture', () => {
  const componentsDir = join(process.cwd(), 'src', 'components');
  describe.each([
    ['skills', 'Skills feature folder'],
    ['salaryCalculator', 'Salary Calculator feature folder'],
    ['configurations', 'Configurations feature folder'],
    ['core', 'Core components folder']
  ])('%s', (featureName, description) => {
    it(`${description} should be self-contained (no external component dependencies)`, () => {
      const featurePath = join(componentsDir, featureName);
      const violations = validateFeatureFolder(featurePath, featureName);
      if (violations.length > 0) {
        const errorMessage = violations.map(v => 
          `\n  ❌ ${v.file}\n     Import: "${v.importPath}"\n     Reason: ${v.reason}`
        ).join('\n');
        expect.fail(
          `Found ${violations.length} architectural violation(s) in ${featureName}:${errorMessage}\n`
        );
      }
      expect(violations).toHaveLength(0);
    });

    it('should have a corresponding test file for each implementation file', () => {
      const featurePath = join(componentsDir, featureName);
      const implFiles = getFilesRecursively(featurePath);
      const violations = implFiles.filter(file => {
        // Skip index.ts/tsx files if they are just barrel files (optional, but good practice usually, 
        // strictly following user 'each implementation')
        // Let's stick to strict first.
        const dir = dirname(file);
        const name = basename(file);
        const nameNoExt = name.replace(/\.tsx?$/, '');
        const testPathTsx = join(dir, '__tests__', `${nameNoExt}.test.tsx`);
        const testPathTs = join(dir, '__tests__', `${nameNoExt}.test.ts`);
        return !existsSync(testPathTsx) && !existsSync(testPathTs);
      });
      if (violations.length > 0) {
        const errorMessage = violations.map(v => 
          `\n  ❌ ${relative(process.cwd(), v)}\n     Reason: Missing test file in ./__tests__/${basename(v).replace(/\.tsx?$/, '.test.tsx')}`
        ).join('\n');
        expect.fail(
          `Found ${violations.length} missing test file(s):${errorMessage}\n`
        );
      }
      expect(violations).toHaveLength(0);
    });

  });

  describe('Test File Location', () => {
    it('should have all test files located in ./__tests__ directories', () => {
      const allTestFiles = getTestFiles(componentsDir);
      const violations = allTestFiles.filter(file => {
        const parentDir = basename(dirname(file));
        return parentDir !== '__tests__';
      });
      if (violations.length > 0) {
        const errorMessage = violations.map(v => 
          `\n  ❌ ${relative(process.cwd(), v)}\n     Reason: Test files must be located in a __tests__ directory`
        ).join('\n');
        expect.fail(
          `Found ${violations.length} test file location violation(s):${errorMessage}\n`
        );
      }
      expect(violations).toHaveLength(0);
    });
  });
});
