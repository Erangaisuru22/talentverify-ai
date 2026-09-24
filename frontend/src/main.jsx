/**
 * @file main.jsx
 * @description Application entry point for TalentVerifyAI frontend.
 * Sets up global CSS, catches critical boot errors using an ErrorBoundary,
 * and mounts the root React component tree into the DOM.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

/**
 * Top-level React Error Boundary to capture unhandled rendering crashes
 * and present a recovery UI instead of a blank screen.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  // Update state so the next render will show the fallback UI
  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    // If no error occurred, render children normally
    if (!this.state.error) return this.props.children

    // Fallback error UI shown upon runtime failure
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
        <section className="w-full max-w-lg rounded-2xl bg-white p-8 text-center shadow-2xl">
          <h1 className="text-2xl font-bold text-slate-900">TalentVerifyAI could not start</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">Clear this site's browser data, reload the page, and restart the app with <code className="rounded bg-slate-100 px-1.5 py-1">npm.cmd run dev</code> if needed.</p>
          <button type="button" onClick={() => window.location.reload()} className="mt-6 rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white hover:bg-blue-700">Reload page</button>
          <details className="mt-6 text-left text-xs text-slate-500"><summary className="cursor-pointer font-semibold">Technical details</summary><pre className="mt-2 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-100 p-3">{String(this.state.error?.message || this.state.error)}</pre></details>
        </section>
      </main>
    )
  }
}

// Locate root DOM element container
const root = document.getElementById('root')
if (!root) throw new Error('The application root element is missing.')

// Mount React application inside StrictMode and ErrorBoundary
ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <ErrorBoundary><App /></ErrorBoundary>
  </React.StrictMode>,
)

