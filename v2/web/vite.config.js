import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// 100 % offline : aucun CDN, toutes les libs sont bundlées en local par le build
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8787' },
  },
  build: { outDir: 'dist', sourcemap: false },
});
