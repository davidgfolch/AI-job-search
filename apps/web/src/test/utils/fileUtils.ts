import { readdirSync, statSync, existsSync } from 'fs';
import { join } from 'path';

/**
 * Get all TypeScript/TSX files in a directory recursively
 */
export function getFilesRecursively(dir: string, fileList: string[] = []): string[] {
  if (!existsSync(dir)) return [];
  const files = readdirSync(dir);
  files.forEach((file: string) => {
    const filePath = join(dir, file);
    if (statSync(filePath).isDirectory()) {
      if (file !== 'node_modules' && file !== 'test' && file !== 'dist' && file !== 'build') {
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
export function getTestFiles(dir: string, fileList: string[] = []): string[] {
  if (!existsSync(dir)) return [];
  const files = readdirSync(dir);
  files.forEach((file: string) => {
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
