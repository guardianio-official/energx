import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: { // Optional: configure server if needed, e.g. for proxy
    port: 3000, // Frontend dev server port
    // proxy: {
    //   '/api': {
    //     target: 'http://localhost:5000', // Assuming backend runs on 5000
    //     changeOrigin: true,
    //   }
    // }
  }
})
