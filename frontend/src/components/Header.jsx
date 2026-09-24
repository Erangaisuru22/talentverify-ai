/**
 * @file Header.jsx
 * @description Top navigation bar displayed across authenticated dashboard and profile views.
 * Houses brand identity, active view navigation toggles (Dashboard vs Profile), and logout action.
 */

import React from 'react';
import { LayoutDashboard, LogOut, User } from 'lucide-react';
import BrandLogo from './BrandLogo';

/**
 * Header component providing application navigation and session logout.
 *
 * @param {Object} props
 * @param {string} props.page - Current active page view ('dashboard' | 'profile').
 * @param {(page: string) => void} props.onNavigate - Callback invoked when navigation tabs are clicked.
 * @param {() => void} props.onLogout - Callback to terminate the user session.
 */
export default function Header({ page, onNavigate, onLogout }) {
  return (
    <header className="sticky top-0 z-40 flex items-center justify-between gap-2 border-b border-slate-200 bg-white/95 px-3 py-3 shadow-sm backdrop-blur sm:px-6">
      {/* Brand Identity / Logo */}
      <BrandLogo />

      {/* Navigation Controls & Session Actions */}
      <div className="flex shrink-0 items-center gap-1 sm:gap-3">
        {/* Dashboard / Home Navigation Button */}
        <button
          onClick={() => onNavigate('dashboard')}
          className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition ${
            page === 'dashboard' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <LayoutDashboard size={17} />
          <span className="hidden md:inline">Home</span>
        </button>

        {/* Profile Settings Navigation Button */}
        <button
          onClick={() => onNavigate('profile')}
          className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition ${
            page === 'profile' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <User size={17} />
          <span className="hidden md:inline">Profile</span>
        </button>

        {/* Session Logout Button */}
        <button
          onClick={onLogout}
          className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
        >
          <LogOut size={17} />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </header>
  );
}

