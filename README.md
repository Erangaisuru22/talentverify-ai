# TalentVerify AI — Frontend Module
**Lead Developer:** Eranga Isuru Bandara

The Frontend module of TalentVerify AI provides an interactive, responsive Single Page Application (SPA) designed for candidates and recruiters.

---

## Key Features

1. **Candidate Dashboard:**
   - Real-time job search and filtering.
   - Interactive CV upload (PDF/DOCX/TXT) with Gemini AI skill extraction.
   - Instant compatibility analysis and match scoring without exposing internal recruiter formulas.
   - Application lifecycle tracking and withdrawal modal.

2. **Recruiter Dashboard:**
   - Multi-dimensional candidate evaluation cards.
   - Interactive applicant ranking and score sorting.
   - Evaluation versioning (`Evaluation Version 1`, `Version 2`) and re-evaluation triggers.
   - Score override controls with audit justification logs.
   - Job post creation, editing, and deletion (Cascading cleanup for demo recruiter).

3. **Authentication & Session Security:**
   - Clean, modern Login & Registration interface.
   - Tab-scoped session persistence using `sessionStorage` (auto-logout on window/tab close).

---

## Tech Stack

- **Framework:** React 18
- **Build Tool:** Vite
- **Styling:** TailwindCSS & Custom Modern CSS
- **Icons:** Lucide React
- **API Client:** Native Fetch / REST Client

---

## How to Run Frontend

```bash
cd frontend
npm install
npm run dev
```

The application will start at `http://127.0.0.1:5173`.
