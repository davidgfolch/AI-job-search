/// <reference types="vitest" />
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import fs from 'fs'
import { BackendResolver } from './src/common/backendResolver.ts'
import { BackendWatchdog } from './src/common/backendWatchdog.ts'

// https://vite.dev/config/
export default defineConfig(async ({ mode, command }) => {
  // In Docker: /app is WORKDIR, .env is mounted at /workspace/.env
  // In local dev: resolve from __dirname (apps/web) up two levels to monorepo root
  let envDir: string;
  
  if (fs.existsSync('/workspace/.env')) {
    // Running in Docker container
    envDir = '/workspace';
  } else {
    // Running locally
    envDir = path.resolve(import.meta.dirname, '../../');
  }
  
  console.log('🔍 import.meta.dirname:', import.meta.dirname)
  console.log('🔍 Vite env directory:', envDir)
  console.log('🔍 Mode:', mode)
  
  const env = loadEnv(mode, envDir, '')
  console.log('🔍 AI_ENRICHSKILL_ENABLED from loadEnv:', env.AI_ENRICHSKILL_ENABLED)
  
  const aiEnrichSkillEnabled = env.AI_ENRICHSKILL_ENABLED === 'True' || env.AI_ENRICHSKILL_ENABLED === 'true'
  console.log('🔍 aiEnrichSkillEnabled:', aiEnrichSkillEnabled)

  // Vitest loads this config as well: never block on the backend there, and never
  // start the watchdog, otherwise the test run would wait for a running backend.
  const isTestRun = mode === 'test' || process.env.VITEST !== undefined
  const resolver = new BackendResolver({ env })

  // The dev server waits for the backend to answer before it starts serving, so a
  // container start (or a host reboot) never ends up proxying to a dead target.
  const apiTarget = command === 'serve' && !isTestRun ? await resolver.resolve() : resolver.target

  // Vite keeps this exact object and spreads it on every proxied request, so
  // mutating `target` retargets the live proxy without restarting the server.
  const proxyConfig = { target: apiTarget, changeOrigin: true }

  if (command === 'serve' && !isTestRun) {
    const watchdog = new BackendWatchdog({
      check: () => resolver.isReachable(),
      reconnect: () => resolver.reconnect(),
      current: () => resolver.target,
      onChange: (url: string) => { proxyConfig.target = url },
      checkIntervalMs: resolver.config.checkIntervalMs,
      maxFailures: resolver.config.maxRetries,
    })
    watchdog.start()
    console.log('🔍 Backend watchdog started, interval:', resolver.config.checkIntervalMs, 'ms, retries:', resolver.config.maxRetries)
  }

  return {
    define: {
      __AI_ENRICH_SKILL_ENABLED__: aiEnrichSkillEnabled ? 'true' : 'false',
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
      '/api': proxyConfig
    }
  },
  test: {
    globals: true,
    testTimeout: 15000,
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
      // Without `include`, V8 only reports modules a test actually imported, so a
      // lazily-routed page that no test imports (dashboard, company synonyms)
      // vanishes from the denominator instead of counting as 0%.
      include: ['src/**/*.ts', 'src/**/*.tsx'],
      // Test code lives in `test/` folders; keeping it out of the denominator is
      // what makes the number reflect production code.
      exclude: ['**/node_modules/**', '**/dist/**', '**/test/**', '**/*.css'],
      thresholds: {
        lines: 90,
        statements: 90,
      },
    }
  },
  }
})
