import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '10.76.126.11',
    proxy: {
      '/api': {
        target: 'http://10.76.126.24:5000',
        changeOrigin: true,
      },
    },
  },
})
