import { defineConfig } from 'vite'
import { resolve } from 'node:path'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss()],
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
