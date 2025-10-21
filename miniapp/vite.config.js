import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/giftbottg/',  // 👈 Название твоего репозитория
  build: {
    outDir: '../docs',  // 👈 Собираем в корневую папку docs/
    emptyOutDir: false, // Не удаляем rules.html
    sourcemap: false,
    minify: 'terser',
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