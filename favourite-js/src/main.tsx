import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'
import './i18n'
import { initDatabase } from './core/database'

// Initialize database before rendering
initDatabase().then(() => {
  console.log('Database initialized successfully')
  
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </React.StrictMode>,
  )
}).catch((err) => {
  console.error('Failed to initialize database:', err)
})
