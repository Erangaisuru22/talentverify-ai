/**
 * @file App.jsx
 * @description Main application controller and root container.
 * Manages global user authentication state, session token storage,
 * high-level data synchronization (jobs, applications, profile),
 * and page-level routing between Public/Landing, Auth, Profile, and Role-specific Dashboards.
 */

import React, { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import CandidateDashboard from './pages/CandidateDashboard';
import RecruiterDashboard from './pages/RecruiterDashboard';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import LandingPage from './pages/LandingPage';
import Header from './components/Header';
import { apiRequest } from './services/api';

/** Session storage key used for temporary in-tab session persistence */
const TOKEN_KEY = 'tv_session_token';

/**
 * Reads the authentication token safely from sessionStorage.
 * Clears any legacy localStorage token to ensure sessions close when the tab is closed.
 * @returns {string} The stored token or an empty string.
 */
function readToken() {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
    return window.sessionStorage.getItem(TOKEN_KEY) || '';
  } catch {
    return '';
  }
}

/**
 * Stores or clears the authentication token in sessionStorage.
 * Automatically cleared by the browser when the tab or window is closed.
 * @param {string} token - The active session token (cleared if falsy).
 */
function storeToken(token) {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
    if (token) window.sessionStorage.setItem(TOKEN_KEY, token);
    else window.sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    /* Keep working gracefully even if browser storage is restricted. */
  }
}

export default function App() {
  // --- Global Application States ---
  const [token, setToken] = useState(readToken); // Active user session token
  const [user, setUser] = useState(null);         // Current authenticated user object
  const [jobs, setJobs] = useState([]);           // List of available job postings
  const [applications, setApplications] = useState([]); // List of user's or recruiter's applications
  const [page, setPage] = useState('dashboard');   // Current page view ('dashboard' | 'profile')
  const [loading, setLoading] = useState(Boolean(token)); // Global initialization loading state
  const [startupError, setStartupError] = useState('');   // Error message if initial boot fails
  const [authMode, setAuthMode] = useState(null);  // Auth modal/view mode: null | 'login' | 'register'

  /**
   * Effect: Synchronizes application data on initial mount or when token changes.
   * If unauthenticated, fetches public job listings for the landing page.
   * If authenticated, loads user profile, jobs, and applications.
   */
  useEffect(() => {
    if (!token) {
      setLoading(true);
      apiRequest('/api/public/jobs')
        .then((data) => setJobs(data || []))
        .catch(() => setJobs([]))
        .finally(() => setLoading(false));
      return;
    }

    // Authenticated state: Fetch user session and initial data bundle
    apiRequest(`/api/app-data?token=${encodeURIComponent(token)}`)
      .then((data) => {
        setUser(data.user);
        setJobs(data.jobs || []);
        setApplications(data.applications || []);
      })
      .catch((error) => {
        // Token invalidated or expired: Reset session
        storeToken('');
        setToken('');
        setUser(null);
        setStartupError(error.message);
      })
      .finally(() => setLoading(false));
  }, [token]);

  /**
   * Handles user authentication (login or registration).
   * @param {Object} credentials - Username/email, password, role, etc.
   * @returns {Promise<{error?: string}>} Object containing error message if failed.
   */
  const handleAuth = async (credentials) => {
    try {
      const result = await apiRequest('/api/auth', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });
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
   * Updates the authenticated user's profile details.
   * @param {Object} profile - Updated profile payload.
   */
  const saveProfile = async (profile) => {
    const updated = await apiRequest(`/api/profile?token=${encodeURIComponent(token)}`, {
      method: 'PATCH',
      body: JSON.stringify({ data: profile }),
    });
    setUser(updated);
    return updated;
  };

  /**
   * Recruiter: Creates a new job posting.
   * @param {Object} job - New job configuration.
   */
  const addJob = async (job) => {
    const created = await apiRequest(`/api/jobs?token=${encodeURIComponent(token)}`, {
      method: 'POST',
      body: JSON.stringify({ data: job }),
    });
    setJobs((current) => [created, ...current]);
  };

  /**
   * Recruiter: Updates an existing job posting.
   * @param {string|number} jobId - Target job identifier.
   * @param {Object} changes - Modified properties.
   */
  const updateJob = async (jobId, changes) => {
    const updated = await apiRequest(`/api/jobs/${jobId}?token=${encodeURIComponent(token)}`, {
      method: 'PATCH',
      body: JSON.stringify({ data: changes }),
    });
    setJobs((current) => current.map((job) => (job.id === jobId ? updated : job)));
  };

  /**
   * Recruiter: Deletes an existing job posting.
   * @param {string|number} jobId - Target job identifier.
   */
  const deleteJob = async (jobId) => {
    await apiRequest(`/api/jobs/${jobId}?token=${encodeURIComponent(token)}`, {
      method: 'DELETE',
    });
    setJobs((current) => current.filter((job) => job.id !== jobId));
    setApplications((current) => current.filter((app) => app.jobId !== jobId));
  };

  /**
   * Candidate: Submits a new job application.
   * @param {Object} application - Application submission data.
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
   * @param {string|number} applicationId - Application ID to withdraw.
   */
  const withdrawApplication = async (applicationId) => {
    await apiRequest(`/api/applications/${applicationId}?token=${encodeURIComponent(token)}`, {
      method: 'DELETE',
    });
    setApplications((current) => current.filter((item) => item.id !== applicationId));
  };

  /**
   * Recruiter: Updates the processing status of an application.
   * @param {string|number} applicationId - Target application ID.
   * @param {string} status - New status (e.g., Shortlisted, Interviewing, Rejected).
   */
  const updateApplicationStatus = async (applicationId, status) => {
    const updated = await apiRequest(`/api/applications/${applicationId}/status?token=${encodeURIComponent(token)}`, {
      method: 'PATCH',
      body: JSON.stringify({ data: { status } }),
    });
    setApplications((current) => current.map((item) => (item.id === applicationId ? updated : item)));
  };

  /**
   * Clears the current user session and returns to the public landing page.
   */
  const logout = async () => {
    try {
      await apiRequest(`/api/session?token=${encodeURIComponent(token)}`, { method: 'DELETE' });
    } catch {
      /* Always clear local credentials regardless of backend session deletion result */
    }
    storeToken('');
    setToken('');
    setUser(null);
    setJobs([]);
    setApplications([]);
    setPage('dashboard');
  };

  // --- View Rendering Logic ---

  // 1. Unauthenticated and user requested Login or Sign Up
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

  // 2. Unauthenticated landing page view
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

  // 3. Full-screen loading indicator during state transitions
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  // 4. Authenticated application layout with dynamic view routing
  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 font-sans flex flex-col">
      {/* Top Navigation Bar */}
      <Header page={page} onNavigate={setPage} onLogout={logout} />

      {/* Main Content Area */}
      <main className="mx-auto w-full max-w-7xl flex-1 px-3 py-4 sm:px-6 sm:py-6 lg:px-8">
        {page === 'profile' ? (
          // Shared User Profile Settings Page
          <ProfilePage user={user} token={token} onSave={saveProfile} />
        ) : user.role === 'recruiter' ? (
          // Recruiter Dashboard: Job Management & Applicant Tracking (Admin sees all platform jobs)
          <RecruiterDashboard
            user={user}
            token={token}
            jobs={
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
          // Candidate Dashboard: Profile Verification, Job Search & Application Tracking
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


