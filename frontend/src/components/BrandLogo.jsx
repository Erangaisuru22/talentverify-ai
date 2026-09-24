/**
 * @file BrandLogo.jsx
 * @description Renders the TalentVerifyAI brand logo with icon and optional text mark.
 * Supports inverse contrast theme for dark navigation bars/hero backgrounds and compact mode.
 */

import React from 'react';

/**
 * Brand logo component displaying the shield checkmark icon and product name.
 *
 * @param {Object} props
 * @param {boolean} [props.inverse=false] - When true, adjusts colors for dark backgrounds.
 * @param {boolean} [props.compact=false] - When true, hides the text label and only shows the icon.
 */
export default function BrandLogo({ inverse = false, compact = false }) {
  return (
    <div className="flex items-center gap-3" aria-label="TalentVerifyAI">
      {/* Brand Icon (Shield with verification checkmark) */}
      <span
        className={`relative flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-xl shadow-sm ${
          inverse ? 'bg-white text-blue-700' : 'bg-gradient-to-br from-blue-600 to-indigo-700 text-white'
        }`}
      >
        <svg viewBox="0 0 40 40" className="h-8 w-8" fill="none" aria-hidden="true">
          {/* Shield outline */}
          <path
            d="M20 4.5 32 9v9.2c0 8-5 14.2-12 17.3-7-3.1-12-9.3-12-17.3V9l12-4.5Z"
            fill="currentColor"
            fillOpacity=".14"
            stroke="currentColor"
            strokeWidth="2"
          />
          {/* Verification checkmark */}
          <path
            d="m13.5 20 4.1 4.1 8.9-9"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Accent dot */}
          <circle cx="29.5" cy="10.5" r="3" className={inverse ? 'fill-cyan-500' : 'fill-cyan-300'} />
        </svg>
      </span>

      {/* Brand Text Typography */}
      {!compact && (
        <span
          className={`hidden text-xl font-extrabold tracking-tight min-[430px]:inline ${
            inverse ? 'text-white' : 'text-slate-900'
          }`}
        >
          TalentVerify
          <span className={inverse ? 'text-cyan-300' : 'text-blue-600'}>AI</span>
        </span>
      )}
    </div>
  );
}

