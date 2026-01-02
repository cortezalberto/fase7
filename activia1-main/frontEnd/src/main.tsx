/**
 * Main Entry Point - React 19
 *
 * React 19 introduces a new root API that is simpler and more intuitive.
 * The createRoot API remains the same but with improved error handling.
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// React 19: createRoot API with improved error boundaries
const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error(
    'Root element not found. Make sure there is a <div id="root"></div> in your index.html'
  );
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);