import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Modern Tailwind v4 Engine Integration
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  server: {
    host: '0.0.0.0',
    port: 5173
  }
})
