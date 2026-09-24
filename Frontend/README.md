# README File

## Project Structure

```
Frontend/
├── index.html                  # Standalone HTML prototype (non-React)
├── style.css                   # Global design tokens & utility styles
├── app.js                      # Vanilla JS for the HTML prototype
├── talentverify_react.html     # React CDN prototype
├── vite.config.js              # Vite configuration
├── package.json
│
└── src/
    ├── main.jsx                # React entry point
    ├── index.css               # React app global styles
    ├── App.jsx                 # Root component & page registry
    │
    ├── components/             # Shared UI components
    │   ├── HeaderCandidate.jsx
    │   ├── HeaderPublic.jsx
    │   ├── PageSwitcher.jsx
    │   └── SidebarRecruiter.jsx
    │
    └── pages/                  # Full-page screen components (20 pages)
        ├── Landing.jsx
        ├── PublicJobs.jsx
        ├── RegisterCandidate.jsx
        ├── RegisterRecruiter.jsx
        ├── SignIn.jsx
        ├── CandidateDashboard.jsx
        ├── CandidateProfile.jsx
        ├── CandidateResumes.jsx
        ├── CandidateJobs.jsx
        ├── CandidateApplications.jsx
        ├── CandidateUpdates.jsx
        ├── CandidateAIAssistant.jsx
        ├── RecruiterDashboard.jsx
        ├── RecruiterJobs.jsx
        ├── RecruiterCandidates.jsx
        ├── RecruiterCandidateProfile.jsx
        ├── RecruiterMatching.jsx
        ├── RecruiterResumeUpload.jsx
        ├── RecruiterSettings.jsx
        └── PageNotFound.jsx
```

---
