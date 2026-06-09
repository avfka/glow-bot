import '@fontsource-variable/inter';
import './index.css';

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { App } from './app/App';
import { initTelegram } from './lib/telegram';

const inTelegram = initTelegram();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App inTelegram={inTelegram} />
  </StrictMode>,
);
