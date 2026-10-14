import { defineConfig } from 'vite'
import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss()],
  // Library builds do not define process.env.NODE_ENV, so react-dom's
  // production/development switch referenced a `process` global that browsers
  // do not have: the built bundle threw "ReferenceError: process is not
  // defined" and the custom element never registered. Pin it to production for
  // the embed build only (define is a top-level Vite option, not a build key).
  define: mode === 'embed'
    ? { 'process.env.NODE_ENV': JSON.stringify('production') }
    : undefined,
  build: mode === 'embed'
    ? {
        emptyOutDir: true,
        lib: {
          entry: resolve(__dirname, 'src/embed.tsx'),
          name: 'AIWebsiteAssistant',
          formats: ['es', 'iife'],
          fileName: (format) => `ai-website-assistant.${format}.js`,
        },
      }
    : undefined,
}))
