export interface ImportViolation {
  file: string;
  importPath: string;
  reason: string;
}

/**
 * Extract import statements from TypeScript/TSX files
 */
export function extractImports(content: string): string[] {
  const imports: string[] = [];
  const importRegex = /import\s+(?:[\w\s{},*]*\s+from\s+)?['"](.*?)['"]/g;
  let match;
  while ((match = importRegex.exec(content)) !== null) {
    imports.push(match[1]);
  }
  return imports;
}
