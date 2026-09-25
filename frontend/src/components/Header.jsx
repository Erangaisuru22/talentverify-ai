/**
 * ============================================================================
 * @file Header.jsx
 * @description Top navigation bar displayed across authenticated views.
 * 
 * CORE RESPONSIBILITIES:
 * 1. Displays company brand identity via `<BrandLogo />`.
 * 2. Provides active page navigation between Dashboard (Home) and Profile.
 * 3. Provides clean session logout triggering credential clearing and redirect.
 * ============================================================================
 */

// ----------------------------------------------------------------------------
// JavaScript Keyword: `import`
// Pulls in React and UI vector icons from the lucide-react package.
// ----------------------------------------------------------------------------
import React from 'react';
import { LayoutDashboard, LogOut, User } from 'lucide-react';
import BrandLogo from './BrandLogo';

/**
 * ----------------------------------------------------------------------------
 * JavaScript Keywords: `export default function`
 * - `export default`: Exposes Header as the main export of this component file.
 * - `function`: Functional React component accepting destructured props.
 * ----------------------------------------------------------------------------
 * Header Component.
 *
 * @param {Object} props - Destructured component properties.
 * @param {string} props.page - Current active page route identifier ('dashboard' | 'profile').
 * @param {(page: string) => void} props.onNavigate - Callback function to update current page.
 * @param {() => void} props.onLogout - Callback function to terminate user session.
 * @returns {React.ReactElement} Navigation header JSX markup.
 */
export default function Header({ page, onNavigate, onLogout }) {
  // JavaScript Keyword: `return`
  // Returns HTML5 semantic `<header>` element with responsive Tailwind CSS classes.
  return (
    <header className="sticky top-0 z-40 flex items-center justify-between gap-2 border-b border-slate-200 bg-white/95 px-3 py-3 shadow-sm backdrop-blur sm:px-6">
      {/* Brand Identity / Logo Component */}
      <BrandLogo />

      {/* Navigation Controls & Session Actions Container */}
      <div className="flex shrink-0 items-center gap-1 sm:gap-3">
        {/* 
          1. Dashboard / Home Navigation Button
          - JavaScript Event: `onClick` triggers an inline arrow function `() => onNavigate('dashboard')`
          - JavaScript Template Literal: ``${expression}`` dynamically applies active styling
        */}
        <button
          onClick={() => onNavigate('dashboard')}
          className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition ${
            page === 'dashboard' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <LayoutDashboard size={17} />
          <span className="hidden md:inline">Home</span>
        </button>

        {/* 
          2. Profile Settings Navigation Button
          - Switches view to the user profile settings and evidence verification center
        */}
        <button
          onClick={() => onNavigate('profile')}
          className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold transition ${
            page === 'profile' ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <User size={17} />
          <span className="hidden md:inline">Profile</span>
        </button>

        {/* 
          3. Session Logout Button
          - Terminates active session and resets state back to landing page
        */}
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
