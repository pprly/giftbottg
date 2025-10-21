import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/giftbottg/',
  build: {
    outDir: '../docs',
    emptyOutDir: false,
    sourcemap: false,
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'telegram-vendor': ['@telegram-apps/sdk-react', '@telegram-apps/telegram-ui']
        }
      }
    }
  },
  server: {
    host: true,
    port: 5173
  }
})