import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/giftbottg/',  // 👈 Название твоего репозитория
  root: './',
  publicDir: 'public',
  build: {
    outDir: '../docs',  // 👈 Собираем в корневую папку docs/
    emptyOutDir: false, // Не удаляем rules.html
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      input: resolve(__dirname, 'public/index.html'), // 👈 Явно указываем путь к HTML
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