import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig({plugins:[react(),tailwindcss()],server:{watch:{ignored:(path)=>path.toLowerCase().endsWith('.cmd')},proxy:{'/api':'http://127.0.0.1:3001'}},build:{outDir:'dist'}});
