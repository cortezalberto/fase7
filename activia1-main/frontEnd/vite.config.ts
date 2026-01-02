import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
// FE-BUILD-001 to FE-BUILD-005: Build optimizations applied
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@/components': path.resolve(__dirname, './src/components'),
      '@/services': path.resolve(__dirname, './src/services'),
      '@/types': path.resolve(__dirname, './src/types'),
      '@/hooks': path.resolve(__dirname, './src/hooks'),
      '@/utils': path.resolve(__dirname, './src/utils'),
      '@/contexts': path.resolve(__dirname, './src/contexts'),
      '@/lib': path.resolve(__dirname, './src/lib'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.warn('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.warn('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.warn('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
  // FE-BUILD-001: Production build optimizations
  build: {
    // Terser for better minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.log in production
        drop_debugger: true,
        pure_funcs: ['console.info', 'console.debug', 'console.warn'],
      },
      mangle: {
        safari10: true,
      },
    },
    // FE-BUILD-002: Code splitting with manual chunks
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks for better caching
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-ui': ['lucide-react', 'clsx', 'tailwind-merge'],
          'vendor-utils': ['zustand', 'axios'],
        },
      },
    },
    // FE-BUILD-003: Chunk size warnings
    chunkSizeWarningLimit: 500,
    // FE-BUILD-004: Source maps for production debugging
    sourcemap: false,  // Disable in production for smaller builds
    // FE-BUILD-005: Asset optimization
    assetsInlineLimit: 4096,  // Inline assets < 4kb as base64
    cssCodeSplit: true,  // Split CSS per chunk
    reportCompressedSize: false,  // Faster builds
  },
  // FE-BUILD-004: Optimize deps for faster dev server
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom', 'zustand', 'axios', 'lucide-react'],
  },
  // Enable esbuild for faster builds
  esbuild: {
    legalComments: 'none',  // Remove license comments
  },
})