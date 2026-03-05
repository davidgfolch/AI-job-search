/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // In Docker: /app is WORKDIR, .env is mounted at /workspace/.env
  // In local dev: resolve from __dirname (apps/web) up two levels to monorepo root
  let envDir: string;
  
  if (fs.existsSync('/workspace/.env')) {
    // Running in Docker container
    envDir = '/workspace';
  } else {
    // Running locally
    envDir = path.resolve(__dirname, '../../');
  }
  
  console.log('🔍 __dirname:', __dirname)
  console.log('🔍 Vite env directory:', envDir)
  console.log('🔍 Mode:', mode)
  
  const env = loadEnv(mode, envDir, '')
  console.log('🔍 AI_ENRICHNEW_SKILL from loadEnv:', env.AI_ENRICHNEW_SKILL)
  
  const aiEnrichSkillEnabled = env.AI_ENRICHNEW_SKILL === 'True' || env.AI_ENRICHNEW_SKILL === 'true'
  console.log('🔍 aiEnrichSkillEnabled:', aiEnrichSkillEnabled)


  const isDocker = fs.existsSync('/workspace/.env');
  const apiTarget = isDocker ? 'http://backend:8000' : 'http://localhost:8000';

  return {
    define: {
      __AI_ENRICHNEW_SKILL_ENABLED__: aiEnrichSkillEnabled ? 'true' : 'false',
      __TEST_CONSTANT__: 'true',
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
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      }
    }
  },
  test: {
    globals: true,
    environment: 'jsdom',
    environmentOptions: {
      jsdom: {
        url: 'http://localhost',
      },
    },
    setupFiles: './src/pages/viewer/test/setup.ts',
    css: true,
    exclude: ['**/node_modules/**', '**/tests/**'],
    cache: true,
    coverage: {
      reporter: ['text', 'json-summary', 'json'],
      reportOnFailure: true,
      thresholds: {
        lines: 85,
        statements: 85,
      },
    }
  },
  }
})
