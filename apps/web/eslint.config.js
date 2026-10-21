import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

// Test suites, fixtures and mocks: `any` is tolerated there and fast-refresh does not apply.
const testGlobs = [
  '**/*.test.{ts,tsx}',
  '**/*.spec.{ts,tsx}',
  '**/test/**/*.{ts,tsx}',
  '**/tests/**/*.{ts,tsx}',
  '**/__tests__/**/*.{ts,tsx}',
  '**/mocks/**/*.{ts,tsx}',
  '**/test-utils.{ts,tsx}',
  '**/testUtils.{ts,tsx}',
  '**/*TestUtils.{ts,tsx}',
  '**/*Mocks.{ts,tsx}',
  '**/*.fixtures.{ts,tsx}',
]

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      // Unused code is the enforced gate. A leading underscore marks an intentionally unused argument.
      '@typescript-eslint/no-unused-vars': ['error', {
        argsIgnorePattern: '^_',
        varsIgnorePattern: '^_',
        caughtErrorsIgnorePattern: '^_',
      }],
      '@typescript-eslint/no-explicit-any': 'error',
      // React Compiler oriented rules: reported, but not blocking until the components are migrated.
      'react-hooks/exhaustive-deps': 'warn',
      'react-hooks/immutability': 'warn',
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
  {
    files: testGlobs,
    rules: {
      '@typescript-eslint/no-explicit-any': 'warn',
      'react-refresh/only-export-components': 'off',
    },
  },
])
