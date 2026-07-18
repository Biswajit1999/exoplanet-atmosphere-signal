import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    // The atmospheric transit scene is optional and loaded after the report shell.
    chunkSizeWarningLimit: 850,
  },
});
