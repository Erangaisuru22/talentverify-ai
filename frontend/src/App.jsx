import React, { useEffect, useState } from 'react';
import { LayoutDashboard, Loader2, LogOut, User } from 'lucide-react';
import CandidateDashboard from './components/CandidateDashboard';
import RecruiterDashboard from './components/RecruiterDashboard';
import LoginPage from './components/LoginPage';
import ProfilePage from './components/ProfilePage';
import BrandLogo from './components/BrandLogo';
import LandingPage from './components/LandingPage';
import { apiRequest } from './services/api';

const TOKEN_KEY = 'tv_session_token';

function readToken() {
  try { return window.localStorage.getItem(TOKEN_KEY) || ''; } catch { return ''; }
}

function storeToken(token) {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch { /* Keep working when browser storage is blocked. */ }
}

export default function App() {
  const [token, setToken] = useState(readToken);
  const [user, setUser] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [page, setPage] = useState('dashboard');
  const [loading, setLoading] = useState(Boolean(token));
  const [startupError, setStartupError] = useState('');
  const [authMode, setAuthMode] = useState(null);

  useEffect(() => {
    if (!token) {
      setLoading(true);
      apiRequest('/api/public/jobs').then((data) => setJobs(data || [])).catch(() => setJobs([])).finally(() => setLoading(false));
      return;
    }
    apiRequest(`/api/app-data?token=${encodeURIComponent(token)}`).then((data) => {
      setUser(data.user); setJobs(data.jobs || []); setApplications(data.applications || []);
    }).catch((error) => {
      storeToken(''); setToken(''); setUser(null); setStartupError(error.message);
    }).finally(() => setLoading(false));
  }, [token]);

  const handleAuth = async (credentials) => {
    try {
      const result = await apiRequest('/api/auth', { method: 'POST', body: JSON.stringify(credentials) });
      storeToken(result.token); setStartupError(''); setToken(result.token); setUser(result.user);
      return {};
    } catch (error) { return { error: error.message }; }
  };

  const saveProfile = async (profile) => {
    const updated = await apiRequest(`/api/profile?token=${encodeURIComponent(token)}`, { method: 'PATCH', body: JSON.stringify({ data: profile }) });
    setUser(updated); return updated;
  };
  const addJob = async (job) => {
    const created = await apiRequest(`/api/jobs?token=${encodeURIComponent(token)}`, { method: 'POST', body: JSON.stringify({ data: job }) });
    setJobs((current) => [created, ...current]);
  };
  const updateJob = async (jobId, changes) => {
    const updated = await apiRequest(`/api/jobs/${jobId}?token=${encodeURIComponent(token)}`, { method: 'PATCH', body: JSON.stringify({ data: changes }) });
    setJobs((current) => current.map((job) => job.id === jobId ? updated : job));
  };
  const addApplication = async (application) => {
    const created = await apiRequest(`/api/applications?token=${encodeURIComponent(token)}`, { method: 'POST', body: JSON.stringify({ data: application }) });
    setApplications((current) => [created, ...current]);
    return created;
  };
  const withdrawApplication = async (applicationId) => {
    await apiRequest(`/api/applications/${applicationId}?token=${encodeURIComponent(token)}`, { method: 'DELETE' });
    setApplications((current) => current.filter((item) => item.id !== applicationId));
  };
  const updateApplicationStatus = async (applicationId, status) => {
    const updated = await apiRequest(`/api/applications/${applicationId}/status?token=${encodeURIComponent(token)}`, { method: 'PATCH', body: JSON.stringify({ data: { status } }) });
    setApplications((current) => current.map((item) => item.id === applicationId ? updated : item));
  };
  const logout = async () => {
    try { await apiRequest(`/api/session?token=${encodeURIComponent(token)}`, { method: 'DELETE' }); } catch { /* Always clear the local token. */ }
    storeToken(''); setToken(''); setUser(null); setJobs([]); setApplications([]); setPage('dashboard');
  };

  if (!user && authMode) return <LoginPage onLogin={handleAuth} initialError={startupError} initialMode={authMode} onBack={() => { setAuthMode(null); setStartupError(''); }} />;
  if (!user) return <LandingPage jobs={jobs} loading={loading} onSignIn={() => setAuthMode('login')} onCreateAccount={() => setAuthMode('register')} onApply={() => setAuthMode('login')} />;
  if (loading) return <div className="flex min-h-screen items-center justify-center bg-slate-950 text-white"><Loader2 className="animate-spin" size={32} /></div>;

  return <div className="min-h-screen bg-slate-50 text-slate-800 font-sans flex flex-col">
    <header className="sticky top-0 z-40 flex items-center justify-between gap-2 border-b border-slate-200 bg-white/95 px-3 py-3 shadow-sm backdrop-blur sm:px-6"><BrandLogo /><div className="flex shrink-0 items-center gap-1 sm:gap-3">
      <button onClick={() => setPage('dashboard')} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold ${page === 'dashboard' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'}`}><LayoutDashboard size={17}/><span className="hidden md:inline">Home</span></button>
      <button onClick={() => setPage('profile')} className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold ${page === 'profile' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'}`}><User size={17}/><span className="hidden md:inline">Profile</span></button>
      <button onClick={logout} className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"><LogOut size={17}/><span className="hidden sm:inline">Logout</span></button>
    </div></header>
    <main className="mx-auto w-full max-w-7xl flex-1 px-3 py-4 sm:px-6 sm:py-6 lg:px-8">
      {page === 'profile' ? <ProfilePage user={user} token={token} onSave={saveProfile}/> : user.role === 'recruiter' ? <RecruiterDashboard user={user} token={token} jobs={jobs.filter((job) => job.recruiterId === user.id)} applications={applications} onAddJob={addJob} onUpdateJob={updateJob} onUpdateApplicationStatus={updateApplicationStatus}/> : <CandidateDashboard jobs={jobs} user={user} token={token} applications={applications.filter((item) => !['Withdrawn', 'Application Withdrawn'].includes(item.status))} onSaveProfile={saveProfile} onApply={addApplication} onWithdraw={withdrawApplication} onNavigateProfile={() => setPage('profile')}/>} 
    </main>
  </div>;
}
