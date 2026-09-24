<div align="center">

# 💻 TalentVerify AI — Frontend Module
### Modern React 18 Single Page Application (SPA)

[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.0-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Lucide](https://img.shields.io/badge/Lucide_Icons-React-F56565?style=for-the-badge)](https://lucide.dev)

<p align="center">
  <b>Lead Developer:</b> Eranga Isuru Bandara<br>
  <b>Branch:</b> <code>Eranga</code>
</p>

</div>

---

## 📖 Module Overview

The **Frontend Module** of TalentVerify AI delivers an intuitive, high-performance user experience for both Job Candidates and Hiring Recruiters. Built with **React 18** and bundled with **Vite**, it features dynamic role-based dashboards, instant CV analysis visualization, glassmorphism design accents, and tab-isolated session security.

---

## 🔑 Key Features & User Interfaces

### 1. 👨‍💻 Candidate Dashboard (`src/pages/CandidateDashboard.jsx`)
- **Real-Time Job Discovery:** Filter and search active job listings by title, company, skills, or location.
- **AI-Powered CV Upload:** Drag-and-drop support for PDF, DOCX, and TXT resumes with automatic text parsing via Google Gemini AI.
- **Dynamic Compatibility Visualizer:** Displays circular match score (0–100%), Match Level badge (*Strong*, *Moderate*, *Low*), and Evidence Confidence percentage.
- **Privacy-First Scoring:** Internal recruiter marks, weights, and rubric calculations are hidden; candidates see only their overall match percentage and career guidance.
- **Application Lifecycle Tracking:** View submitted applications, review evaluation summaries, and safely withdraw applications with modal confirmation.

### 2. 👔 Recruiter Dashboard (`src/pages/RecruiterDashboard.jsx`)
- **Job Vacancy Management:** Create, edit, and delete job postings with custom skill tags, required experience, and weighted evaluation criteria.
- **Cascade Deletion:** Privileged demo recruiter (`recruiter@gmail.com`) can delete jobs with automatic cascading cleanup of linked applications.
- **Applicant Ranking & Sorting:** Instantly sort applicants by AI match score ascending or descending.
- **Multi-Source Technical Skills Matrix:** Inspect candidate skills verified against real GitHub commits, portfolio links, and CV claims.
- **Evaluation Versioning & Audit Trail:** Track versioned score trajectory (`Version 1`, `Version 2`) and re-evaluate applicants with latest evidence on-demand.
- **Human Decision Overrides:** Documented score adjustment controls requiring an audit justification.

### 3. 🔐 Authentication & Session Security (`src/pages/LoginPage.jsx` & `src/App.jsx`)
- Seamless sign-in and account registration for Candidates and Recruiters.
- **Tab-Scoped `sessionStorage`:** Eliminates persistent token leakage. Closing the browser tab or window automatically logs out the user.

---

## 📂 Source Code Architecture

```
frontend/
├── index.html                   # HTML entry point with modern viewport meta tags
├── vite.config.js               # Vite build configuration & server port proxy
├── tailwind.config.js           # Tailwind utility design tokens
├── postcss.config.js            # PostCSS autoprefixer pipeline
├── package.json                 # Dependencies (React, Lucide, Tailwind, Vite)
└── src/
    ├── main.jsx                 # React root DOM hydration
    ├── index.css                # Global stylesheet & design tokens
    ├── App.jsx                  # Root view orchestrator & session state manager
    │
    ├── components/              # Shared Reusable UI Components
    │   ├── Header.jsx           # Global navigation header with role badge & logout
    │   └── BrandLogo.jsx        # Responsive SVG brand logo
    │
    ├── pages/                   # Application Screen Views
    │   ├── CandidateDashboard.jsx # Job search, CV parsing, & candidate application review
    │   ├── RecruiterDashboard.jsx # Candidate ranking, evaluation versioning, overrides
    │   ├── LoginPage.jsx        # Role-based sign-in & sign-up forms
    │   ├── ProfilePage.jsx      # Candidate skills, experience, & GitHub profile editor
    │   └── LandingPage.jsx      # Public promotional landing page
    │
    └── services/
        └── api.js               # Centralized REST API client (Fetch wrapper)
```

---

## 🚀 How to Run Locally

### 1. Install Node Dependencies
```powershell
cd frontend
npm install
```

### 2. Start Vite Development Server
```powershell
npm run dev
```
The application will launch with Hot Module Replacement (HMR) at:  
👉 **http://127.0.0.1:5173**

### 3. Build Production Bundle
```powershell
npm run build
```
Generates an optimized, minified production build in the `frontend/dist/` directory.
