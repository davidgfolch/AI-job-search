import { readFileSync } from 'fs';
import { dirname, resolve, normalize, join, relative } from 'path';
import type { ImportViolation } from './importUtils';
import { extractImports } from './importUtils';
import { getFilesRecursively } from './fileUtils';

/**
 * Check if an import violates feature folder self-containment rules
 */
export function checkImportViolation(
  importPath: string,
  featureName: string,
  currentFilePath: string,
  featureFolderPath: string
): string | null {
  if (!importPath.startsWith('.')) {
    return null;
  }
  const currentDir = dirname(currentFilePath);
  const resolvedPath = normalize(resolve(currentDir, importPath));
  const normalizedFeaturePath = normalize(featureFolderPath);
  if (!resolvedPath.startsWith(normalizedFeaturePath)) {
    const commonFeaturePath = normalize(join(process.cwd(), 'src', 'pages', 'common'));
    if (resolvedPath.startsWith(commonFeaturePath)) {
      return null;
    }
    if (resolvedPath.includes('\\hooks\\') || resolvedPath.includes('/hooks/')) {
      return 'Imports from sibling hooks directory. Use internal hooks instead.';
    }
    if (resolvedPath.includes('\\utils\\') || resolvedPath.includes('/utils/')) {
      return 'Imports from sibling utils directory. Use internal utils instead.';
    }
    const featureFolders = ['skillsManager', 'viewer', 'statistics', 'common'];
    const otherFeatures = featureFolders.filter(f => f !== featureName);
    for (const otherFeature of otherFeatures) {
      if (resolvedPath.includes(`\\pages\\${otherFeature}\\`) || resolvedPath.includes(`/pages/${otherFeature}/`)) {
        return `Imports from other feature folder (${otherFeature}). Features should be self-contained.`;
      }
    }
  }
  return null;
}

/**
 * Validate that a feature folder doesn't have forbidden dependencies
 */
export function validateFeatureFolder(featurePath: string, featureName: string): ImportViolation[] {
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
