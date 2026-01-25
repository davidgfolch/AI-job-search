/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, path.resolve(process.cwd(), '../../'), '')
  const aiEnrichSkillEnabled = env.AI_ENRICH_SKILL === 'True' || env.AI_ENRICH_SKILL === 'true'

  return {
    define: {
      __AI_ENRICH_SKILL_ENABLED__: JSON.stringify(aiEnrichSkillEnabled),
    },
    plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true,
      interval: 1000,
    },
    hmr: {
      host: 'localhost',
      port: 5173,
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    environmentOptions: {
      jsdom: {
        url: 'http://localhost',
      },
    },
    setupFiles: './src/test/setup.ts',
    css: true,
    exclude: ['**/node_modules/**', '**/tests/**'],
    coverage: {
      reporter: ['text', 'json-summary', 'json'],
      reportOnFailure: true,
    }
  },
  }
})
