import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The UI talks to the FastAPI backend; in development requests to /api are proxied.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: { chunkSizeWarningLimit: 2500 },
})
