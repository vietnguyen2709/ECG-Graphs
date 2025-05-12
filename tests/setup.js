import { vi } from 'vitest'

// Mock browser globals
global.alert = vi.fn()
global.fetch = vi.fn()
global.FormData = class FormData {
  constructor() {
    this.data = {}
  }
  append(key, value) {
    this.data[key] = value
  }
}

// This setup file runs before all tests
console.log('Setting up test environment...')
