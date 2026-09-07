import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (!this.state.error) return this.props.children
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

const root = document.getElementById('root')
if (!root) throw new Error('The application root element is missing.')

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <ErrorBoundary><App /></ErrorBoundary>
  </React.StrictMode>,
)
