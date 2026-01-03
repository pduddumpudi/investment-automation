import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // Use relative paths for GitHub Pages
  build: {
    outDir: '../docs', // Build to docs folder for GitHub Pages
    emptyOutDir: false, // Don't delete data folder
    rollupOptions: {
      output: {
        manualChunks: undefined, // Keep everything in one bundle for simplicity
      },
    },
  },
  publicDir: false, // Don't copy public folder, we manage data separately
})
