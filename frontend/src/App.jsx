/**
 * ============================================================================
 * @file App.jsx
 * @description Main application controller and root container for TalentVerifyAI.
 * 
 * CORE RESPONSIBILITIES:
 * 1. Global User Authentication & Session State Management.
 * 2. High-Level Data Synchronization (Jobs, Applications, User Profile).
 * 3. Page-Level Conditional View Routing (Landing, Auth, Profile, Dashboards).
 * ============================================================================
 */

// ----------------------------------------------------------------------------
// JavaScript Keyword: `import`
// Purpose: Used to import functions, objects, or components exported from 
// external modules or libraries into the current file scope.
// ----------------------------------------------------------------------------
// React core library and Hooks:
// - `useEffect`: React Hook to perform side effects (data fetching, subscriptions).
// - `useState`: React Hook to track state in functional components.
import React, { useEffect, useState } from 'react';

// External UI Icon library (lucide-react):
import { Loader2 } from 'lucide-react';

// Application Pages & Sub-views:
import CandidateDashboard from './pages/CandidateDashboard';
import RecruiterDashboard from './pages/RecruiterDashboard';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import LandingPage from './pages/LandingPage';

// Shared Layout Components:
import Header from './components/Header';

// Centralized Backend Communication Service:
import { apiRequest } from './services/api';

// ----------------------------------------------------------------------------
// JavaScript Keyword: `const`
// Purpose: Declares a block-scoped variable whose reference cannot be reassigned.
// ----------------------------------------------------------------------------
/** Key used to store active session authentication token in browser storage */
const TOKEN_KEY = 'tv_session_token';

/**
 * ----------------------------------------------------------------------------
 * JavaScript Keyword: `function`
 * Purpose: Declares an executable block of code with specified parameters.
 * ----------------------------------------------------------------------------
 * Helper function to retrieve the active session token safely from sessionStorage.
 * Clears any old localStorage token to enforce in-tab session lifecycle.
 *
 * @returns {string} The active authentication token, or an empty string if none.
 */
function readToken() {
  // JavaScript Keyword: `try...catch`
  // Purpose: Handles runtime exceptions gracefully without breaking program execution.
  try {
    // Remove token from persistent localStorage (security: auto-closes when tab shuts)
    window.localStorage.removeItem(TOKEN_KEY);
    // Read and return the session token from active tab's sessionStorage
    return window.sessionStorage.getItem(TOKEN_KEY) || '';
  } catch {
    // JavaScript Keyword: `return`
    // Purpose: Terminates function execution and returns a specified value.
    return '';
  }
}

/**
 * Helper function to store or clear the authentication token in sessionStorage.
 *
 * @param {string} token - The active session token string (or empty/falsy to clear).
 */
function storeToken(token) {
  try {
    // Clear any token from localStorage
    window.localStorage.removeItem(TOKEN_KEY);
    // JavaScript Keyword: `if...else`
    // Purpose: Conditional execution based on whether a truthy condition is met.
    if (token) {
      window.sessionStorage.setItem(TOKEN_KEY, token);
    } else {
      window.sessionStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    /* Keep working gracefully even if browser security restricts web storage access. */
  }
}

/**
 * ----------------------------------------------------------------------------
 * JavaScript Keywords: `export default`
 * Purpose: Designates the primary export of this module so other files can 
 * import it using: `import App from './App.jsx'`.
 * ----------------------------------------------------------------------------
 * Root Application Component.
 */
export default function App() {
  // --------------------------------------------------------------------------
  // REACT STATE HOOKS (`useState`)
  // Syntax: `const [stateVariable, setterFunction] = useState(initialValue);`
  // Purpose: Triggers a component re-render whenever the setter function is called.
  // --------------------------------------------------------------------------

  // 1. Session token state (initialized from browser sessionStorage)
  const [token, setToken] = useState(readToken);

  // 2. Authenticated user object (null when unauthenticated)
  const [user, setUser] = useState(null);

  // 3. Array of active job postings available on the platform
  const [jobs, setJobs] = useState([]);

  // 4. Array of job applications submitted by candidates or viewed by recruiters
  const [applications, setApplications] = useState([]);

  // 5. Active page view navigation route ('dashboard' | 'profile')
  const [page, setPage] = useState('dashboard');

  // 6. Global loading spinner flag (true during initial startup/session verification)
  const [loading, setLoading] = useState(Boolean(token));

  // 7. Startup error message string if server connection or initial boot fails
  const [startupError, setStartupError] = useState('');

  // 8. Authentication modal mode: null (landing) | 'login' (sign in) | 'register' (sign up)
  const [authMode, setAuthMode] = useState(null);

  // --------------------------------------------------------------------------
  // REACT LIFECYCLE HOOK (`useEffect`)
  // Purpose: Runs side effects (such as fetching API data) after the component renders.
  // Dependency Array `[token]`: Re-runs this effect whenever `token` changes.
  // --------------------------------------------------------------------------
  useEffect(() => {
    // Condition 1: User is unauthenticated (no token present)
    if (!token) {
      setLoading(true);
      // Fetch public job listings for the landing page showcase
      apiRequest('/api/public/jobs')
        // Promise `.then()`: Executes upon successful HTTP resolution
        .then((data) => setJobs(data || []))
        // Promise `.catch()`: Executes if network or API error occurs
        .catch(() => setJobs([]))
        // Promise `.finally()`: Executes regardless of success or failure
        .finally(() => setLoading(false));
      return; // Exit effect early
    }

    // Condition 2: User is authenticated (token exists)
    // Fetch user profile, company jobs, and candidate applications in one bundle
    apiRequest(`/api/app-data?token=${encodeURIComponent(token)}`)
      .then((data) => {
        setUser(data.user);
        setJobs(data.jobs || []);
        setApplications(data.applications || []);
      })
      .catch((error) => {
        // If the token is expired or invalidated by the server, reset session
        storeToken('');
        setToken('');
        setUser(null);
        setStartupError(error.message);
      })
      .finally(() => setLoading(false));
  }, [token]);

  // --------------------------------------------------------------------------
  // ASYNCHRONOUS ACTION HANDLERS
  // JavaScript Keywords: `async` and `await`
  // Purpose: `async` defines a function that returns a Promise.
  // `await` pauses execution non-blockingly until the Promise resolves or rejects.
  // --------------------------------------------------------------------------

  /**
   * Handles user authentication (Login or Register).
   * 
   * @param {Object} credentials - Username/email, password, role, etc.
   * @returns {Promise<{error?: string}>} Object containing error message if failed.
   */
  const handleAuth = async (credentials) => {
    try {
      // POST authentication request to FastAPI backend
      const result = await apiRequest('/api/auth', {
        method: 'POST',
        // JavaScript Method: `JSON.stringify` converts JS object into JSON string
        body: JSON.stringify(credentials),
      });

      // Persist session credentials into state and storage
      storeToken(result.token);
      setStartupError('');
      setToken(result.token);
      setUser(result.user);
      return {};
    } catch (error) {
      return { error: error.message };
    }
  };

  /**
   * Updates the candidate or recruiter user profile details in the database.
   * 
   * @param {Object} profile - Updated profile fields.
   * @returns {Promise<Object>} Updated user profile data from server.
   */
  const saveProfile = async (profile) => {
    const updated = await apiRequest(`/api/profile?token=${encodeURIComponent(token)}`, {
      method: 'PATCH',
      body: JSON.stringify({ data: profile }),
    });
    // Update local state with latest user details from server
    setUser(updated);
    return updated;
  };

  /**
   * Recruiter: Creates a new job posting on the platform.
   * 
   * @param {Object} job - New job details (title, description, skills, location, type).
   */
  const addJob = async (job) => {
    const created = await apiRequest(`/api/jobs?token=${encodeURIComponent(token)}`, {
      method: 'POST',
      body: JSON.stringify({ data: job }),
    });
    // State Updater Function: `(current) => [newItem, ...current]`
    // Prepend newly created job to the front of the list
    setJobs((current) => [created, ...current]);
  };

  /**
   * Recruiter: Updates an existing job posting.
   * 
   * @param {string|number} jobId - Identifier of the job to update.
   * @param {Object} changes - Modified properties.
   */
  const updateJob = async (jobId, changes) => {
    const updated = await apiRequest(`/api/jobs/${jobId}?token=${encodeURIComponent(token)}`, {
      method: 'PATCH',
      body: JSON.stringify({ data: changes }),
    });
    // Array Method `.map()`: Replaces the matching item while keeping others intact
    setJobs((current) => current.map((job) => (job.id === jobId ? updated : job)));
  };

  /**
   * Recruiter / Platform Admin: Deletes an existing job posting and linked records.
   * 
   * @param {string|number} jobId - Identifier of the job to delete.
   */
  const deleteJob = async (jobId) => {
    await apiRequest(`/api/jobs/${jobId}?token=${encodeURIComponent(token)}`, {
      method: 'DELETE',
    });
    // Array Method `.filter()`: Retains all items except the one matching jobId
    setJobs((current) => current.filter((job) => job.id !== jobId));
    setApplications((current) => current.filter((app) => app.jobId !== jobId));
  };

  /**
   * Candidate: Submits a new job application with evidence and skills snapshot.
   * 
   * @param {Object} application - Application payload.
   * @returns {Promise<Object>} Created application record.
   */
  const addApplication = async (application) => {
    const created = await apiRequest(`/api/applications?token=${encodeURIComponent(token)}`, {
      method: 'POST',
      body: JSON.stringify({ data: application }),
    });
    setApplications((current) => [created, ...current]);
    return created;
  };

  /**
   * Candidate: Withdraws a previously submitted application.
   * 
   * @param {string|number} applicationId - Application ID to withdraw.
   */
  const withdrawApplication = async (applicationId) => {
    await apiRequest(`/api/applications/${applicationId}?token=${encodeURIComponent(token)}`, {
      method: 'DELETE',
    });
    setApplications((current) => current.filter((item) => item.id !== applicationId));
  };

  /**
   * Recruiter: Updates applicant hiring pipeline status (Shortlisted, Reviewing, etc.).
   * 
   * @param {string|number} applicationId - Target application ID.
   * @param {string} status - New pipeline status string.
   */
  const updateApplicationStatus = async (applicationId, status) => {
    const updated = await apiRequest(`/api/applications/${applicationId}/status?token=${encodeURIComponent(token)}`, {
      method: 'PATCH',
      body: JSON.stringify({ data: { status } }),
    });
    setApplications((current) => current.map((item) => (item.id === applicationId ? updated : item)));
  };

  /**
   * Session Termination (Logout): Clears local authentication state and redirects to landing page.
   */
  const logout = async () => {
    try {
      // Invalidate session on server
      await apiRequest(`/api/session?token=${encodeURIComponent(token)}`, { method: 'DELETE' });
    } catch {
      /* Always purge client-side credentials even if backend deletion fails */
    }
    storeToken('');
    setToken('');
    setUser(null);
    setJobs([]);
    setApplications([]);
    setPage('dashboard');
  };

  // --------------------------------------------------------------------------
  // CONDITIONAL VIEW RENDERING
  // Evaluates application state to determine which top-level page component to render.
  // --------------------------------------------------------------------------

  // 1. Unauthenticated user clicked 'Sign In' or 'Create Account' -> Show Login/Register Page
  if (!user && authMode) {
    return (
      <LoginPage
        onLogin={handleAuth}
        initialError={startupError}
        initialMode={authMode}
        onBack={() => {
          setAuthMode(null);
          setStartupError('');
        }}
      />
    );
  }

  // 2. Unauthenticated user on root URL -> Show Public Landing Page
  if (!user) {
    return (
      <LandingPage
        jobs={jobs}
        loading={loading}
        onSignIn={() => setAuthMode('login')}
        onCreateAccount={() => setAuthMode('register')}
        onApply={() => setAuthMode('login')}
      />
    );
  }

  // 3. User is authenticated, but data is currently synchronizing -> Show Animated Loader
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  // 4. Authenticated state -> Main Application Dashboard & Navigation Shell
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans flex flex-col">
      {/* Top Application Header Navigation Bar */}
      <Header page={page} onNavigate={setPage} onLogout={logout} />

      {/* Main Viewport Container */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-3 py-4 sm:px-6 sm:py-6 lg:px-8">
        {/* Ternary Operator: `condition ? ifTrue : ifFalse` */}
        {page === 'profile' ? (
          // View 1: Shared User Profile & Verification Center
          <ProfilePage user={user} token={token} onSave={saveProfile} />
        ) : user.role === 'recruiter' ? (
          // View 2: Recruiter Dashboard (Platform Admin sees all platform jobs)
          <RecruiterDashboard
            user={user}
            token={token}
            jobs={
              // Platform Admin check: recruiter@gmail.com / REC-001 gets full platform access
              user.role === 'admin' || user.email === 'recruiter@gmail.com' || user.id === 'REC-001'
                ? jobs
                : jobs.filter((job) => job.recruiterId === user.id)
            }
            applications={applications}
            onAddJob={addJob}
            onUpdateJob={updateJob}
            onDeleteJob={deleteJob}
            onDeleteApplication={async (applicationId) => {
              await apiRequest(`/api/applications/${applicationId}?token=${encodeURIComponent(token)}`, {
                method: 'DELETE',
              });
              setApplications((current) => current.filter((item) => item.id !== applicationId));
            }}
            onUpdateApplicationStatus={updateApplicationStatus}
          />
        ) : (
          // View 3: Candidate Dashboard: Job Discovery, CV parsing, and Application Tracking
          <CandidateDashboard
            jobs={jobs}
            user={user}
            token={token}
            applications={applications.filter((item) => !['Withdrawn', 'Application Withdrawn'].includes(item.status))}
            onSaveProfile={saveProfile}
            onApply={addApplication}
            onWithdraw={withdrawApplication}
            onNavigateProfile={() => setPage('profile')}
          />
        )}
      </main>
    </div>
  );
}
