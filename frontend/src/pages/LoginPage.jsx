/**
 * @file LoginPage.jsx
 * @description Authentication screen handling both User Sign In and Account Registration.
 * Supports distinct role creation (Candidate vs Recruiter) with dynamic form validation,
 * password visibility toggling, and contextual error rendering.
 */

import React, { useState } from 'react';
import { ArrowLeft, ArrowRight, Briefcase, Eye, EyeOff, ShieldCheck, User } from 'lucide-react';
import BrandLogo from '../components/BrandLogo';

/**
 * LoginPage Component for authentication.
 *
 * @param {Object} props
 * @param {(credentials: Object) => Promise<{error?: string}>} props.onLogin - Authentication submission handler.
 * @param {string} [props.initialError=''] - Startup or initial auth error string.
 * @param {'login'|'register'} [props.initialMode='login'] - Initial view mode.
 * @param {() => void} [props.onBack] - Handler to navigate back to the public job board.
 */
export default function LoginPage({ onLogin, initialError = '', initialMode = 'login', onBack }) {
  // --- Form State Management ---
  const [mode, setMode] = useState(initialMode);         // 'login' or 'register'
  const [role, setRole] = useState('candidate');         // 'candidate' or 'recruiter' (for registration)
  const [name, setName] = useState('');                 // User full name
  const [email, setEmail] = useState('');               // User email address
  const [password, setPassword] = useState('');         // Account password
  const [company, setCompany] = useState('');           // Recruiter's organization name
  const [location, setLocation] = useState('');         // Recruiter's organization location
  const [showPassword, setShowPassword] = useState(false); // Password reveal visibility flag
  const [error, setError] = useState(initialError);     // Validation or API error alert text
  const [submitting, setSubmitting] = useState(false);   // Submission in-progress loading indicator

  /**
   * Validates user inputs and submits the authentication credentials to App.jsx.
   * @param {React.FormEvent} event - HTML form submit event.
   */
  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    // 1. Check required fields based on active mode and role
    if ((mode === 'register' && (!name.trim() || (role === 'recruiter' && (!company.trim() || !location.trim())))) || !email.trim() || !password) {
      setError('Please complete all required fields.');
      return;
    }

    // 2. Format validation: Email
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError('Please enter a valid email address.');
      return;
    }

    // 3. Format validation: Minimum password length
    if (password.length < 6) {
      setError('Password must contain at least 6 characters.');
      return;
    }

    setSubmitting(true);
    const credentials = { mode, email: email.trim().toLowerCase(), password };
    if (mode === 'register') {
      Object.assign(credentials, { role, name: name.trim(), company: company.trim(), location: location.trim() });
    }

    // Call upstream authentication handler
    const result = await onLogin(credentials);
    if (result?.error) setError(result.error);
    setSubmitting(false);
  };

  return (
    <main className="min-h-screen bg-slate-950 p-4 sm:p-6 lg:p-10">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-6xl overflow-hidden rounded-3xl bg-white shadow-2xl sm:min-h-[calc(100vh-3rem)] lg:grid-cols-[1.05fr_0.95fr]">
        {/* --- Left Promotional Branding Showcase (Visible on Large Screens) --- */}
        <section className="relative hidden overflow-hidden bg-gradient-to-br from-blue-700 via-blue-600 to-indigo-700 p-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10" />
          <div className="absolute -bottom-32 -left-24 h-80 w-80 rounded-full bg-cyan-300/10" />

          <div className="relative"><BrandLogo inverse /></div>

          <div className="relative max-w-md">
            <h1 className="text-4xl font-bold leading-tight">Verifiable talent, objective hiring.</h1>
            <p className="mt-5 text-lg leading-8 text-blue-100">
              Match verified developer skills, projects, and CV evidence powered by AI.
            </p>
          </div>

          <div className="relative flex items-center gap-3 text-sm text-blue-100">
            <ShieldCheck size={19} />
            Your information is protected and securely handled.
          </div>
        </section>

        {/* --- Right Interactive Auth Form Panel --- */}
        <section className="flex items-center justify-center px-6 py-10 sm:px-12 lg:px-16">
          <div className="w-full max-w-md">
            {/* Back button to return to public job board */}
            {onBack && (
              <button
                type="button"
                onClick={onBack}
                className="mb-7 inline-flex items-center gap-2 text-sm font-bold text-slate-500 transition hover:text-blue-700"
              >
                <ArrowLeft size={17}/> Back to jobs
              </button>
            )}

            {/* Mobile Brand Logo */}
            <div className="mb-9 lg:hidden"><BrandLogo /></div>

            {/* Form Heading */}
            <p className="mb-2 text-sm font-bold uppercase tracking-[0.18em] text-blue-600">
              {mode === 'login' ? 'Welcome back' : 'Join TalentVerifyAI'}
            </p>
            <h2 className="text-3xl font-bold tracking-tight text-slate-950">
              {mode === 'login' ? 'Sign in to your account' : 'Create your account'}
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              {mode === 'login' ? 'Use your email and password to continue.' : 'Choose your account type to continue.'}
            </p>

            {/* Role Selection Segmented Control (Registration Only) */}
            {mode === 'register' && (
              <div className="mt-8 grid grid-cols-2 gap-3 rounded-xl bg-slate-100 p-1.5" aria-label="Account type">
                <button
                  type="button"
                  onClick={() => setRole('candidate')}
                  className={`flex items-center justify-center gap-2 rounded-lg px-3 py-3 text-sm font-bold transition ${
                    role === 'candidate' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <User size={18} /> Candidate
                </button>
                <button
                  type="button"
                  onClick={() => setRole('recruiter')}
                  className={`flex items-center justify-center gap-2 rounded-lg px-3 py-3 text-sm font-bold transition ${
                    role === 'recruiter' ? 'bg-white text-blue-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <Briefcase size={18} /> Recruiter
                </button>
              </div>
            )}

            {/* Credential Inputs Form */}
            <form onSubmit={handleSubmit} className={`${mode === 'login' ? 'mt-8' : 'mt-7'} space-y-5`} noValidate>
              {/* Full Name field (Register only) */}
              {mode === 'register' && (
                <div>
                  <label htmlFor="name" className="mb-2 block text-sm font-semibold text-slate-700">
                    {role === 'recruiter' ? 'Your name' : 'Full name'}
                  </label>
                  <input
                    id="name"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    placeholder="Enter your name"
                    className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />
                </div>
              )}

              {/* Recruiter specific organization fields */}
              {mode === 'register' && role === 'recruiter' && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label htmlFor="company" className="mb-2 block text-sm font-semibold text-slate-700">Company name</label>
                    <input
                      id="company"
                      value={company}
                      onChange={(event) => setCompany(event.target.value)}
                      placeholder="Company name"
                      className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    />
                  </div>
                  <div>
                    <label htmlFor="company-location" className="mb-2 block text-sm font-semibold text-slate-700">Company location</label>
                    <input
                      id="company-location"
                      value={location}
                      onChange={(event) => setLocation(event.target.value)}
                      placeholder="City, country"
                      className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                    />
                  </div>
                </div>
              )}

              {/* Email Address */}
              <div>
                <label htmlFor="email" className="mb-2 block text-sm font-semibold text-slate-700">Email address</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder={mode === 'login' ? 'you@example.com' : role === 'candidate' ? 'candidate@example.com' : 'recruiter@company.com'}
                  autoComplete="email"
                  className="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </div>

              {/* Password with Reveal/Hide Toggle */}
              <div>
                <div className="mb-2 flex items-center justify-between">
                  <label htmlFor="password" className="text-sm font-semibold text-slate-700">Password</label>
                  <button type="button" className="text-xs font-semibold text-blue-600 hover:text-blue-700">Forgot password?</button>
                </div>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Enter your password"
                    autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                    className="w-full rounded-xl border border-slate-300 px-4 py-3 pr-12 text-sm outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((visible) => !visible)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-slate-400 hover:text-slate-700"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
                  </button>
                </div>
              </div>

              {/* Error Notice Display */}
              {error && (
                <p className="rounded-lg bg-red-50 px-3 py-2 text-sm font-medium text-red-700" role="alert">
                  {error}
                </p>
              )}

              {/* Submit Action Button */}
              <button
                type="submit"
                disabled={submitting}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3.5 font-bold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 disabled:cursor-wait disabled:opacity-60"
              >
                {submitting
                  ? mode === 'login' ? 'Signing in...' : 'Creating account...'
                  : mode === 'login' ? 'Sign in' : `Create account as ${role === 'candidate' ? 'Candidate' : 'Recruiter'}`}
                <ArrowRight size={18} />
              </button>
            </form>

            {/* Toggle between Sign In and Registration */}
            <p className="mt-7 text-center text-sm text-slate-500">
              {mode === 'login' ? 'New to TalentVerifyAI?' : 'Already have an account?'}{' '}
              <button
                type="button"
                onClick={() => {
                  setMode(mode === 'login' ? 'register' : 'login');
                  setError('');
                }}
                className="font-bold text-blue-600 hover:text-blue-700"
              >
                {mode === 'login' ? 'Create an account' : 'Sign in'}
              </button>
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

