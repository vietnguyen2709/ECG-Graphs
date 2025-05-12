import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  test: {
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['code/frontend/scripts/*.js'],
      exclude: ['node_modules', 'tests'],
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
      reportsDirectory: './coverage'
    },
    include: ['tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    globals: true,
    setupFiles: ['./tests/setup.js']
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './code')
    }
  }
})
