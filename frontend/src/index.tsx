import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

const root = document.getElementById('root') as HTMLElement
if (root) {
  createRoot(root).render(<App />)
}
