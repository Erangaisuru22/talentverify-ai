/**
 * ============================================================================
 * @file main.jsx
 * @description Application bootstrap entry point for TalentVerifyAI.
 * 
 * CORE RESPONSIBILITIES:
 * 1. Imports React 18 DOM root rendering engine and global CSS tokens.
 * 2. Implements top-level React ErrorBoundary class to trap uncaught render exceptions.
 * 3. Mounts the root `<App />` component tree into HTML `<div id="root"></div>`.
 * ============================================================================
 */

// ----------------------------------------------------------------------------
// JavaScript Keyword: `import`
// Purpose: Pulls in dependencies from the React library and local project files.
// ----------------------------------------------------------------------------
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

/**
 * ----------------------------------------------------------------------------
 * JavaScript Keywords: `class` and `extends`
 * - `class`: Declares an Object-Oriented class template in JavaScript.
 * - `extends`: Creates inheritance, making ErrorBoundary inherit from `React.Component`.
 * ----------------------------------------------------------------------------
 * Top-level React Error Boundary Component.
 * Catches errors anywhere in the child component tree, logs them, and renders
 * a user-friendly recovery interface instead of a blank white screen.
 */
class ErrorBoundary extends React.Component {
  /**
   * JavaScript Keyword: `constructor`
   * Method that is automatically executed when a new instance of this class is created.
   * 
   * @param {Object} props - Properties passed to the component.
   */
  constructor(props) {
    // JavaScript Keyword: `super`
    // Calls the constructor of the parent class (`React.Component`) with `props`.
    super(props)

    // JavaScript Keyword: `this`
    // Points to the current instance of ErrorBoundary.
    this.state = { error: null }
  }

  /**
   * JavaScript Keyword: `static`
   * Defines a class-level method that belongs to the class itself, not its instances.
   * React calls this lifecycle method when a descendant component throws an error.
   * 
   * @param {Error} error - The uncaught runtime exception.
   * @returns {Object} Updated state object triggering a fallback render.
   */
  static getDerivedStateFromError(error) {
    return { error }
  }

  /**
   * Component Lifecycle Method: `componentDidCatch`
   * Invoked after an error has been thrown by a descendant component.
   * 
   * @param {Error} error - The error that was thrown.
   * @param {React.ErrorInfo} errorInfo - Component stack trace information.
   */
  componentDidCatch(error, errorInfo) {
    console.error('Captured ErrorBoundary failure:', error, errorInfo);
  }

  /**
   * JavaScript Class Method: `render`
   * Mandatory method for React class components that returns JSX markup to the DOM.
   * 
   * @returns {React.ReactNode} Children components or fallback error recovery UI.
   */
  render() {
    // JavaScript Keyword: `if`
    // If no error occurred during rendering, display child components normally.
    if (!this.state.error) return this.props.children

    // JavaScript Keyword: `return`
    // Returns fallback error UI with reload, session reset, and technical stack details.
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
        <section className="w-full max-w-lg rounded-2xl bg-white p-8 text-center shadow-2xl">
          <h1 className="text-2xl font-bold text-slate-900">TalentVerifyAI could not start</h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Click reload or reset your browser session to resume.
          </p>
          <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3.5 text-left font-mono text-xs text-red-800 break-words">
            <span className="font-bold">Error: </span>
            {String(this.state.error?.message || this.state.error)}
          </div>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white hover:bg-blue-700 shadow-sm"
            >
              Reload page
            </button>
            <button
              type="button"
              onClick={() => {
                localStorage.clear();
                sessionStorage.clear();
                window.location.href = '/';
              }}
              className="rounded-xl border border-slate-300 px-5 py-3 font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
            >
              Clear Session & Reset
            </button>
          </div>
          <details open className="mt-5 text-left text-xs text-slate-500">
            <summary className="cursor-pointer font-semibold">Technical stack trace</summary>
            <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-100 p-3 font-mono text-[11px] text-red-700">
              {String(this.state.error?.stack || this.state.error)}
            </pre>
          </details>
        </section>
      </main>
    )
  }
}

// ----------------------------------------------------------------------------
// APPLICATION MOUNTING LOGIC
// ----------------------------------------------------------------------------
// Locate the single root DOM container in index.html: <div id="root"></div>
const root = document.getElementById('root')

// JavaScript Keywords: `if`, `throw new Error`
// Enforces that the root DOM node must exist, otherwise halts execution immediately.
if (!root) throw new Error('The application root element is missing.')

// Mount React application inside StrictMode and ErrorBoundary
ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <ErrorBoundary><App /></ErrorBoundary>
  </React.StrictMode>,
)
