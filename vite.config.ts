import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { VitePWA } from 'vite-plugin-pwa';
export default defineConfig({base: process.env.BASE_PATH || './',plugins:[react(),tailwindcss(),VitePWA({registerType:'autoUpdate',includeAssets:['apple-touch-icon.png'],manifest:{name:'GO CAL · 포켓몬 GO 캘린더',short_name:'GO CAL',lang:'ko',description:'비공식 개인용 포켓몬 GO 이벤트 캘린더',start_url:'./',scope:'./',display:'standalone',background_color:'#101416',theme_color:'#101416',icons:[{src:'icon-192.png',sizes:'192x192',type:'image/png'},{src:'icon-512.png',sizes:'512x512',type:'image/png',purpose:'any'}]},workbox:{globPatterns:['**/*.{js,css,html,png,svg,woff2}'],navigateFallback:'index.html',cleanupOutdatedCaches:true,runtimeCaching:[{urlPattern:/\/data\/.*\.json(?:\?.*)?$/,handler:'NetworkOnly'}]}})]});
