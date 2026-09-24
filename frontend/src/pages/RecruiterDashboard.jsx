/**
 * @file RecruiterDashboard.jsx
 * @description Comprehensive Recruiter Portal for TalentVerifyAI.
 * Enables recruiters to create/edit jobs with customized AI scoring weights,
 * screen candidate applicants, inspect verified GitHub repositories and code quality,
 * review verified skill matrices, perform candidate snapshot comparisons,
 * record assessment scores and overrides with full audit logs, and update application statuses.
 */

import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  Briefcase,
  CheckCircle,
  CheckCircle2,
  ChevronRight,
  Clock,
  Code,
  Cpu,
  ExternalLink,
  Eye,
  FileCode2,
  FolderGit2,
  GitBranch,
  GitCompare,
  Github,
  GitPullRequest,
  History,
  Layers,
  Loader2,
  MapPin,
  Pencil,
  Plus,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Trash2,
  User,
  X,
  XCircle,
} from 'lucide-react';
import { apiRequest } from '../services/api';

// ============================================================================
// DEFAULT SCORING WEIGHTS CONFIGURATION
// Used when creating a new job to determine how the AI engine scores candidates
// Total weights ideally sum up to 100%

// ============================================================================
const DEFAULT_WEIGHTS = {
  technical_skills: 20,     // Weight for matching candidate skills against job requirements
  experience: 15,           // Weight for relevant years of work experience
  projects: 10,             // Weight for real-world projects & repositories
  education: 5,             // Weight for academic degrees and certifications
  certifications: 5,        // Weight for industry-recognized certifications
  github_evidence: 5,       // Weight for verified GitHub repositories & commit activity
  job_relevance: 10,        // Weight for overall domain and role fit
  technical_assessment: 15, // Weight for technical test / coding assessment results
  structured_interview: 15, // Weight for interview panel evaluation
};

/**
 * RecruiterDashboard Component
 * 
 * Main portal for recruiters to:
 * 1. Post and manage job vacancies
 * 2. Review candidates and AI-calculated match scores
 * 3. Inspect verified technical evidence (GitHub repositories, skill matrices)
 * 4. Compare candidate versions, view evaluation history, and re-evaluate
 * 5. Update application statuses (Shortlisted, Hired, Rejected)
 */
export default function RecruiterDashboard({
  user,                     // Currently logged-in recruiter user object
  token,                    // Authentication JWT token for API requests
  jobs = [],                // Array of jobs posted by this recruiter
  applications: allApplications = [], // List of candidate applications across all jobs
  onAddJob,                 // Callback function to create a new job
  onUpdateJob,              // Callback function to edit an existing job
  onDeleteJob,              // Callback function to delete a job
  onUpdateApplicationStatus,// Callback function to update application status (e.g. hired, rejected)
}) {
  // --------------------------------------------------------------------------
  // STATE MANAGEMENT
  // --------------------------------------------------------------------------

  // Template object for resetting the job creation/edit form
  const emptyJob = {
    title: '',
    company: user.company || '',
    location: user.location || '',
    type: 'Full-time',
    experience: 0,
    skills: '',
    description: '',
    mustHaveSkills: '',
    requiredLanguages: '',
    requiredCertifications: '',
    scoring_weights: DEFAULT_WEIGHTS,
  };

  // Job Form State
  const [showForm, setShowForm] = useState(false);            // Controls visibility of Job Create/Edit modal
  const [form, setForm] = useState(emptyJob);                  // Form input data
  const [editingJobId, setEditingJobId] = useState(null);      // ID of job being edited (null when creating)

  // Application Filtering & Sorting
  const [expandedId, setExpandedId] = useState(null);          // ID of application currently expanded for review
  const [scoreOrder, setScoreOrder] = useState('desc');        // Sort order: 'desc' (highest score first) or 'asc'
  const [selectedJobFilter, setSelectedJobFilter] = useState('all'); // Filter applications by specific job ID

  // Evidence & Modal States
  const [selectedSkillDrillDown, setSelectedSkillDrillDown] = useState(null);       // Selected skill for detailed modal view
  const [showHistoryModal, setShowHistoryModal] = useState(false);                   // Shows snapshot history modal
  const [showCompareModal, setShowCompareModal] = useState(false);                   // Shows candidate version comparison modal
  const [showEvaluationHistoryModal, setShowEvaluationHistoryModal] = useState(false); // Shows AI evaluation audit trail
  const [candidateSnapshots, setCandidateSnapshots] = useState([]);                  // GitHub snapshots for the active candidate
  const [compareData, setCompareData] = useState(null);                              // Result of comparing two GitHub snapshots
  const [compareFromId, setCompareFromId] = useState('');                            // Baseline snapshot ID for comparison
  const [compareToId, setCompareToId] = useState('');                                // Target snapshot ID for comparison
  const [evaluationHistory, setEvaluationHistory] = useState([]);                    // Previous evaluation runs for an application
  const [candidateSkillMatrix, setCandidateSkillMatrix] = useState([]);              // Verified skill breakdown from profile & GitHub
  const [showAllCandidateSkillMatrix, setShowAllCandidateSkillMatrix] = useState(false); // Toggle full skill matrix view
  const [reEvaluating, setReEvaluating] = useState(false);                          // Loading state during AI re-evaluation
  const [actionMessage, setActionMessage] = useState('');                            // Feedback/success/error banner message

  // Privilege check: Demo recruiter account (recruiter@gmail.com / REC-001) can delete and manage job posts
  const isDemoRecruiter = user?.email === 'recruiter@gmail.com' || user?.id === 'REC-001';

  // Delete Job Post Handler (Exclusive to Demo Recruiter)
  const handleDeleteJob = async (job) => {
    if (!window.confirm(`Are you sure you want to delete the job post "${job.title}"?\n\nThis will permanently delete this job and any associated applicant records.`)) {
      return;
    }
    try {
      if (onDeleteJob) {
        await onDeleteJob(job.id);
      } else {
        await apiRequest(`/api/jobs/${job.id}?token=${encodeURIComponent(token)}`, {
          method: 'DELETE',
        });
        window.location.reload();
      }
      setActionMessage(`Job "${job.title}" deleted successfully.`);
    } catch (err) {
      setActionMessage(err.message || 'Failed to delete job.');
    }
  };

  // --------------------------------------------------------------------------
  // FILTERING & DERIVED DATA
  // --------------------------------------------------------------------------

  // Filter applications based on selected job from the dropdown
  const filteredApplications =
    selectedJobFilter === 'all'
      ? allApplications
      : allApplications.filter((application) => String(application.jobId) === selectedJobFilter);

  // Enrich applications with AI suggestion reviews
  const applications = filteredApplications.map((application) => ({
    ...application,
    analysis: {
      ...(application.analysis || {}),
      ai_suggestion: recruiterReviewText(application),
    },
  }));

  // Find the currently expanded candidate application
  const expandedApplication = applications.find((application) => application.id === expandedId);
  const recruiterGuidance = expandedApplication?.analysis?.recruiter_guidance;
  const candidateId = expandedApplication?.candidateId;

  // --------------------------------------------------------------------------
  // EVENT HANDLERS (Job Management & Status Updates)
  // --------------------------------------------------------------------------

  // Update candidate status (e.g., Shortlisted, Hired, Rejected)
  const updateStatus = (id, status) => onUpdateApplicationStatus(id, status);

  // Close the job creation/editing modal and reset the form
  const closeForm = () => {
    setShowForm(false);
    setEditingJobId(null);
    setForm(emptyJob);
  };

  // Open modal to create a new job vacancy
  const openNewJob = () => {
    setEditingJobId(null);
    setForm(emptyJob);
    setShowForm(true);
  };

  // Open modal pre-populated with existing job data for editing
  const openEditJob = (job) => {
    setEditingJobId(job.id);
    setForm({
      title: job.title,
      company: job.company,
      location: job.location,
      type: job.type,
      experience: Number(job.experience || 0),
      skills: job.skills,
      description: job.description,
      mustHaveSkills: (job.must_have_requirements || []).filter((x) => x.type === 'skill').map((x) => x.requirement).join(', '),
      requiredLanguages: (job.must_have_requirements || []).filter((x) => x.type === 'language').map((x) => x.requirement).join(', '),
      requiredCertifications: (job.must_have_requirements || []).filter((x) => x.type === 'certification').map((x) => x.requirement).join(', '),
      scoring_weights: job.scoring_weights || DEFAULT_WEIGHTS,
    });
    setShowForm(true);
  };

  // Calculate sum of scoring weights to ensure total equals 100%
  const weightTotal = Object.values(form.scoring_weights || {}).reduce(
    (sum, value) => sum + Number(value || 0),
    0
  );

  // Handle job form submission (Save new or update existing)
  const submit = (event) => {
    event.preventDefault();
    // Parse comma-separated skills, languages, and certifications into structured requirements
    const requirements = [
      ...form.mustHaveSkills.split(',').filter((x) => x.trim()).map((requirement) => ({ requirement: requirement.trim(), type: 'skill', mandatory: true })),
      ...form.requiredLanguages.split(',').filter((x) => x.trim()).map((requirement) => ({ requirement: requirement.trim(), type: 'language', mandatory: true })),
      ...form.requiredCertifications.split(',').filter((x) => x.trim()).map((requirement) => ({ requirement: requirement.trim(), type: 'certification', mandatory: true })),
      ...(Number(form.experience) > 0 ? [{ requirement: `Minimum ${form.experience} years experience`, type: 'experience', minimum_years: Number(form.experience), mandatory: true }] : []),
    ];
    const payload = { ...form, must_have_requirements: requirements };
    editingJobId ? onUpdateJob(editingJobId, payload) : onAddJob(payload);
    closeForm();
  };

  // --------------------------------------------------------------------------
  // SIDE EFFECTS (Fetch Evidence & Skills for Expanded Candidate)
  // --------------------------------------------------------------------------

  // When a recruiter expands a candidate's application, fetch their verified GitHub snapshots and skill matrix
  useEffect(() => {
    if (!candidateId) {
      setCandidateSnapshots([]);
      setCandidateSkillMatrix([]);
      return;
    }
    // 1. Fetch GitHub snapshots history for technical audit
    apiRequest(`/api/candidates/${candidateId}/github/snapshots?token=${encodeURIComponent(token)}`)
      .then((data) => {
        setCandidateSnapshots(data || []);
        if (data && data.length >= 2) {
          // Default: compare the oldest snapshot against the newest snapshot
          setCompareFromId(data[data.length - 1].snapshot_id);
          setCompareToId(data[0].snapshot_id);
        }
      })
      .catch(() => {});

    // 2. Fetch candidate skill matrix (skills cross-referenced against repos, CV & tests)
    apiRequest(`/api/candidates/${candidateId}/skills/matrix?token=${encodeURIComponent(token)}`)
      .then((data) => setCandidateSkillMatrix(data || []))
      .catch(() => {});
  }, [candidateId, token]);

  // --------------------------------------------------------------------------
  // MODAL HANDLERS (Snapshots, Version Comparison & Evaluation Audit)
  // --------------------------------------------------------------------------

  // Open modal displaying history of technical snapshots captured for this candidate
  const openHistoryModal = () => {
    setShowHistoryModal(true);
  };

  // Open modal allowing recruiter to compare two versions of candidate GitHub activity
  const openCompareModal = async () => {
    if (candidateSnapshots.length >= 2) {
      const fromId = compareFromId || candidateSnapshots[candidateSnapshots.length - 1]?.snapshot_id;
      const toId = compareToId || candidateSnapshots[0]?.snapshot_id;
      try {
        const diff = await apiRequest(
          `/api/candidates/${candidateId}/github/compare?from_id=${fromId}&to_id=${toId}&token=${encodeURIComponent(token)}`
        );
        setCompareData(diff);
      } catch (err) {
        setCompareData(null);
      }
    }
    setShowCompareModal(true);
  };

  // Re-run snapshot comparison when recruiter changes "from" or "to" snapshot selection
  const runCompare = async (fromId, toId) => {
    try {
      const diff = await apiRequest(
        `/api/candidates/${candidateId}/github/compare?from_id=${fromId}&to_id=${toId}&token=${encodeURIComponent(token)}`
      );
      setCompareData(diff);
    } catch (err) {
      setCompareData(null);
    }
  };

  // Open evaluation audit trail showing previous AI scores and changes over time
  const openEvaluationHistory = async (appId) => {
    try {
      const history = await apiRequest(
        `/api/applications/${appId}/evaluations?token=${encodeURIComponent(token)}`
      );
      setEvaluationHistory(history || []);
      setShowEvaluationHistoryModal(true);
    } catch (err) {
      setActionMessage('Could not load evaluation history.');
    }
  };

  // Trigger on-demand AI re-evaluation (e.g. after candidate updates GitHub or job weights change)
  const handleReevaluate = async (appId) => {
    setReEvaluating(true);
    setActionMessage('');
    try {
      const updatedApp = await apiRequest(
        `/api/applications/${appId}/re-evaluate?token=${encodeURIComponent(token)}`,
        { method: 'POST' }
      );
      setActionMessage(`Application re-evaluated to Version ${updatedApp.evaluation_version || 2} successfully!`);
      window.location.reload();
    } catch (err) {
      setActionMessage(err.message || 'Re-evaluation failed.');
    } finally {
      setReEvaluating(false);
    }
  };

  // --------------------------------------------------------------------------
  // RENDER UI
  // --------------------------------------------------------------------------
  return (
    <div className="space-y-6">
      {/* -------------------------------------------------------------------- */}
      {/* 1. DASHBOARD HEADER & NEW JOB ACTION                                 */}
      {/* -------------------------------------------------------------------- */}
      <div className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Recruiter Home</h2>
          <p className="mt-1 text-slate-500">Manage your job offers, review verified candidates, and inspect technical evidence.</p>
        </div>
        <button
          onClick={openNewJob}
          className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 font-semibold text-white hover:bg-blue-700"
        >
          <Plus size={18} />
          Post New Job
        </button>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 2. ACTIVE JOB OFFERS CARDS                                           */}
      {/* Displays all jobs created by the recruiter with an edit action       */}
      {/* -------------------------------------------------------------------- */}
      <section>
        <h3 className="mb-3 text-lg font-bold">
          Your Job Offers <span className="text-sm font-normal text-slate-400">({jobs.length})</span>
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <article key={job.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <h4 className="font-bold">{job.title}</h4>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-green-50 px-2 py-1 text-[10px] font-bold text-green-700">ACTIVE</span>
                  <button
                    onClick={() => openEditJob(job)}
                    className="rounded-lg border border-slate-200 p-1.5 text-slate-500 hover:bg-blue-50 hover:text-blue-700 transition"
                    aria-label={`Edit ${job.title}`}
                    title="Edit Job"
                  >
                    <Pencil size={15} />
                  </button>
                  {isDemoRecruiter && (
                    <button
                      onClick={() => handleDeleteJob(job)}
                      className="rounded-lg border border-red-200 p-1.5 text-red-500 hover:bg-red-50 hover:text-red-700 transition"
                      aria-label={`Delete ${job.title}`}
                      title="Delete Job Post (Demo Recruiter Privilege)"
                    >
                      <Trash2 size={15} />
                    </button>
                  )}
                </div>
              </div>
              <p className="mt-2 text-sm text-slate-500">{job.company}</p>
              <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <MapPin size={14} />
                  {job.location}
                </span>
                <span className="flex items-center gap-1">
                  <Briefcase size={14} />
                  {job.type}
                </span>
                <span>{Number(job.experience || 0)}+ years</span>
              </div>
              <p className="mt-3 text-xs leading-5 text-slate-500">{job.description}</p>
            </article>
          ))}
          {!jobs.length && (
            <div className="col-span-full rounded-xl border-2 border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
              No jobs posted yet. Create your first job offer.
            </div>
          )}
        </div>
      </section>

      {/* -------------------------------------------------------------------- */}
      {/* 3. JOB SELECTION FILTER BAR                                          */}
      {/* Allows recruiter to filter candidate applications by specific job   */}
      {/* -------------------------------------------------------------------- */}
      <div className="flex flex-col gap-3 rounded-xl border border-blue-100 bg-blue-50 p-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-bold text-blue-950">Select job applications</p>
          <p className="mt-1 text-xs text-blue-700">Review each job and its candidates separately.</p>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-bold uppercase text-blue-700">Offered job</label>
          <select
            value={selectedJobFilter}
            onChange={(event) => {
              setSelectedJobFilter(event.target.value);
              setExpandedId(null);
            }}
            className="min-w-72 rounded-lg border border-blue-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-700"
          >
            <option value="all">All jobs ({allApplications.length} applications)</option>
            {jobs.map((job) => (
              <option key={job.id} value={String(job.id)}>
                {job.title} — {allApplications.filter((item) => item.jobId === job.id).length} applied
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* -------------------------------------------------------------------- */}
      {/* 4. CANDIDATE APPLICATIONS LIST                                       */}
      {/* Displays candidates, AI match score, mismatch, status, and deep-dive */}
      {/* -------------------------------------------------------------------- */}
      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        {/* Table Header with Sorting Controls */}
        <div className="flex flex-col gap-4 border-b p-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h3 className="text-lg font-bold">Candidate Applications</h3>
            <p className="mt-1 text-sm text-slate-500">Real applications connected to each job and its verified evidence.</p>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-xs font-bold uppercase text-slate-500">Sort match score</label>
            <select
              value={scoreOrder}
              onChange={(event) => setScoreOrder(event.target.value)}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
            >
              <option value="desc">Highest first</option>
              <option value="asc">Lowest first</option>
            </select>
            <span className="text-sm font-semibold text-slate-500">{applications.length} total</span>
          </div>
        </div>

        {/* List of Applications */}
        <div className="divide-y divide-slate-200">
          {[...applications]
            .sort((a, b) =>
              scoreOrder === 'asc' ? Number(a.score || 0) - Number(b.score || 0) : Number(b.score || 0) - Number(a.score || 0)
            )
            .map((application) => {
              const analysis = application.analysis || {};
              const profile = application.candidateSnapshot || {};
              const expanded = expandedId === application.id;
              const mismatch = Math.max(0, 100 - Number(application.score || 0));
              const githubEvidence = application.githubEvidence || profile.github;
              const hasGithub = Boolean(githubEvidence && githubEvidence.verification_status === 'verified');

              return (
                <article key={application.id}>
                  {/* Candidate Summary Row */}
                  <div className="grid gap-4 p-5 lg:grid-cols-[1.2fr_1fr_auto] lg:items-center">
                    <div className="flex items-center gap-3">
                      <span className="flex h-11 w-11 shrink-0 overflow-hidden items-center justify-center rounded-full bg-blue-50 text-blue-700">
                        {profile.photoVisibleToRecruiters && profile.profilePhotoUrl
                          ? <img src={profile.profilePhotoUrl} alt={`${profile.name || 'Candidate'} profile`} className="h-full w-full object-cover" />
                          : <User size={20} />}
                      </span>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="font-bold text-slate-900">{profile.name || 'Candidate'}</p>
                          {hasGithub && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
                              <ShieldCheck size={12} /> Verified GitHub
                            </span>
                          )}
                          <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-600">
                            v{application.evaluation_version || 1}
                          </span>
                        </div>
                        <p className="text-sm text-slate-500">
                          Applied for <span className="font-semibold text-slate-700">{application.jobTitle}</span>
                        </p>
                        <p className="mt-1 text-xs text-slate-400">
                          {profile.headline || 'No headline'} · {application.candidateExperience || 0} years experience
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <Score label="AI match" value={application.score} good />
                      <Score label="Mismatch" value={mismatch} />
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-amber-50 px-3 py-1.5 text-xs font-bold capitalize text-amber-700">
                        {application.status}
                      </span>
                      <button
                        onClick={() => setExpandedId(expanded ? null : application.id)}
                        className="flex items-center gap-1 rounded-lg border border-blue-200 px-3 py-2 text-xs font-bold text-blue-700 hover:bg-blue-50"
                      >
                        <Eye size={15} />
                        {expanded ? 'Hide Details' : 'Review Details'}
                      </button>
                    </div>
                  </div>

                  {/* ---------------------------------------------------------------- */}
                  {/* EXPANDED CANDIDATE DEEP-DIVE REVIEW PANEL                        */}
                  {/* Shows skills match/gaps, GitHub evidence, AI score & audit tools */}
                  {/* ---------------------------------------------------------------- */}
                  {expanded && (
                    <div className="border-t bg-slate-50/70 p-5 space-y-6">
                      {/* Step A: Basic Candidate Contact Details & Skill Gap Analysis */}
                      <div className="grid gap-5 lg:grid-cols-3">
                        {/* Candidate Personal & Portfolio Info */}
                        <DetailPanel title="Candidate details">
                          <Detail label="Name" value={profile.name} />
                          <Detail label="Headline" value={profile.headline} />
                          <Detail label="Location" value={profile.location} />
                          <Detail label="Phone" value={profile.phone} />
                          <Detail label="CV" value={profile.cvFileName || 'Profile application'} />
                          {profile.portfolioUrl && (
                            <p className="mb-2 text-sm text-slate-600">
                              <span className="font-semibold text-slate-800">Portfolio:</span>{' '}
                              <a
                                href={profile.portfolioUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 break-all font-semibold text-blue-700 hover:underline"
                              >
                                View portfolio <ExternalLink size={13} />
                              </a>
                            </p>
                          )}
                          {application.github_snapshot_id && (
                            <Detail label="GitHub Snapshot" value={application.github_snapshot_id} />
                          )}
                        </DetailPanel>

                        {/* Matched Skills with Job Requirements */}
                        <DetailPanel title="Matched skills">
                          {analysis.matched_skills?.length ? (
                            <TagList items={analysis.matched_skills} tone="green" />
                          ) : (
                            <p className="text-sm text-slate-500">No exact matches recorded.</p>
                          )}
                          <Detail
                            label="Experience"
                            value={`${application.candidateExperience || 0} / ${application.requiredExperience || 0} years`}
                          />
                        </DetailPanel>

                        {/* Missing & Partial Skill Gaps */}
                        <DetailPanel title="Missing / partial skills">
                          {analysis.missing_skills?.length ? (
                            <TagList items={analysis.missing_skills} tone="red" />
                          ) : (
                            <p className="text-sm text-green-700">No missing skills.</p>
                          )}
                          {analysis.partial_skills?.length > 0 && (
                            <div className="mt-3">
                              <p className="mb-2 text-xs font-bold uppercase text-amber-700">Partial matches</p>
                              <TagList items={analysis.partial_skills.map((item) => item.skill)} tone="amber" />
                            </div>
                          )}
                        </DetailPanel>
                      </div>

                      {/* Step B: Evaluation Versioning & On-Demand Re-evaluation Bar */}
                      <div className="rounded-xl border border-indigo-100 bg-white p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-700">
                            <Sparkles size={20} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-sm text-slate-900">
                                Evaluation Version {application.evaluation_version || 1}
                              </h4>
                              {application.previous_evaluation_id && (
                                <span className="text-[11px] text-slate-500">
                                  (Re-evaluated from prior snapshot)
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-slate-500 mt-0.5">
                              Snapshot: <span className="font-mono text-indigo-700">{application.github_snapshot_id || 'Initial'}</span>
                            </p>
                          </div>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            type="button"
                            onClick={() => openEvaluationHistory(application.id)}
                            className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                          >
                            <History size={14} /> Evaluation History
                          </button>
                          <button
                            type="button"
                            disabled={reEvaluating}
                            onClick={() => handleReevaluate(application.id)}
                            className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
                          >
                            {reEvaluating ? (
                              <>
                                <Loader2 size={14} className="animate-spin" /> Re-evaluating...
                              </>
                            ) : (
                              <>
                                <RefreshCw size={14} /> Re-evaluate with Latest Evidence
                              </>
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Gemini Guidance */}
                      <div className="rounded-xl border border-blue-100 bg-blue-50 p-4">
                        <p className="text-xs font-bold uppercase text-blue-700">AI-Assisted Match Assessment</p>
                        <p className="mt-2 text-sm leading-6 text-blue-950">
                          {analysis.ai_suggestion || 'No AI guidance was saved for this application.'}
                        </p>
                      </div>

                      {/* Deep GitHub Evidence Section */}
                      {githubEvidence && (
                        <DetailedGithubEvidenceSection
                          evidence={githubEvidence}
                          snapshots={candidateSnapshots}
                          onOpenSkillDrillDown={(skillData) => setSelectedSkillDrillDown(skillData)}
                          onOpenHistory={openHistoryModal}
                          onOpenCompare={openCompareModal}
                        />
                      )}

                      {/* Multi-Source Skill Matrix */}
                      {candidateSkillMatrix.length > 0 && (
                        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
                          <div className="flex items-center justify-between">
                            <h4 className="flex items-center gap-2 text-sm font-bold text-slate-900">
                              <Layers size={16} className="text-indigo-600" /> Multi-Source Technical Skills Matrix
                            </h4>
                            <span className="text-xs text-slate-400">Aggregated cross-source validation</span>
                          </div>
                          <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs">
                              <thead>
                                <tr className="border-b bg-slate-50 text-slate-600 font-bold uppercase">
                                  <th className="p-2.5">Skill</th>
                                  <th className="p-2.5">Status</th>
                                  <th className="p-2.5">Confidence</th>
                                  <th className="p-2.5">Sources</th>
                                  <th className="p-2.5">Portfolio</th>
                                  <th className="p-2.5">LinkedIn</th>
                                  <th className="p-2.5">Verified Repositories / Evidence</th>
                                  <th className="p-2.5">Action</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100">
                                {(showAllCandidateSkillMatrix ? candidateSkillMatrix : candidateSkillMatrix.slice(0, 32)).map((item, idx) => (
                                  <tr key={idx} className="hover:bg-slate-50/50">
                                    <td className="p-2.5 font-bold text-slate-900">{item.skill}</td>
                                    <td className="p-2.5">
                                      <span
                                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold ${
                                          item.verification_status === 'verified'
                                            ? 'bg-emerald-50 text-emerald-700'
                                            : item.verification_status === 'partially_verified'
                                            ? 'bg-amber-50 text-amber-700'
                                            : 'bg-slate-100 text-slate-600'
                                        }`}
                                      >
                                        {item.verification_status === 'verified' && <CheckCircle2 size={11} />}
                                        {item.verification_status === 'partially_verified' && <AlertTriangle size={11} />}
                                        {item.verification_status?.replaceAll('_', ' ')}
                                      </span>
                                    </td>
                                    <td className="p-2.5">
                                      <span className="font-semibold text-slate-700">
                                        {Math.round((item.confidence || 0) * 100)}%
                                      </span>
                                    </td>
                                    <td className="p-2.5 text-slate-600">
                                      {(item.sources || []).join(', ')}
                                    </td>
                                    <td className="p-2.5">
                                      {item.portfolio_evidence && item.portfolio_url ? (
                                        <a href={item.portfolio_url} target="_blank" rel="noreferrer" className="inline-flex items-center text-indigo-700 hover:underline" title="Portfolio link provided">
                                          Available
                                        </a>
                                      ) : <span className="text-slate-300">—</span>}
                                    </td>
                                    <td className="p-2.5">
                                      {item.linkedin_evidence && item.linkedin_url ? (
                                        <a href={item.linkedin_url} target="_blank" rel="noreferrer" className="inline-flex items-center text-indigo-700 hover:underline" title="LinkedIn profile link provided">
                                          Available
                                        </a>
                                      ) : <span className="text-slate-300">—</span>}
                                    </td>
                                    <td className="p-2.5 text-slate-600 max-w-xs truncate">
                                      {item.repositories?.length > 0
                                        ? item.repositories.join(', ')
                                        : item.notes || 'Documented in CV/Profile'}
                                    </td>
                                    <td className="p-2.5">
                                      {item.evidence && (
                                        <button
                                          type="button"
                                          onClick={() => setSelectedSkillDrillDown(item.evidence)}
                                          className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 underline"
                                        >
                                          Drill Down
                                        </button>
                                      )}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {candidateSkillMatrix.length > 32 && (
                              <button
                                type="button"
                                onClick={() => setShowAllCandidateSkillMatrix((current) => !current)}
                                className="mt-3 w-full rounded-lg border border-indigo-200 py-2 text-xs font-bold text-indigo-700 hover:bg-indigo-50"
                              >
                                {showAllCandidateSkillMatrix ? 'Show less' : `See more (${candidateSkillMatrix.length - 32})`}
                              </button>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Recruiter Score Overrides */}
                      <ScoreOverrides application={application} token={token} />

                      {/* Status Buttons */}
                      <div className="mt-5 flex flex-wrap justify-end gap-2">
                        <StatusButton
                          active={application.status === 'Selected'}
                          color="green"
                          onClick={() => updateStatus(application.id, 'Selected')}
                          icon={<CheckCircle size={17} />}
                        >
                          Select
                        </StatusButton>
                        <StatusButton
                          active={application.status === 'Shortlisted'}
                          color="amber"
                          onClick={() => updateStatus(application.id, 'Shortlisted')}
                          icon={<Clock size={17} />}
                        >
                          Shortlist
                        </StatusButton>
                        <StatusButton
                          active={application.status === 'Rejected'}
                          color="red"
                          onClick={() => updateStatus(application.id, 'Rejected')}
                          icon={<XCircle size={17} />}
                        >
                          Reject
                        </StatusButton>
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
          {!applications.length && (
            <div className="p-10 text-center">
              <User className="mx-auto text-slate-300" size={34} />
              <p className="mt-3 font-semibold text-slate-600">No candidate applications yet</p>
              <p className="mt-1 text-sm text-slate-400">Applications will appear here after candidates analyze and confirm a job.</p>
            </div>
          )}
        </div>
      </section>

      {/* Post/Edit Job Form Modal */}
      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
          <form
            onSubmit={submit}
            className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"
          >
            <div className="mb-6 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold">Post a new job</h3>
                <p className="text-sm text-slate-500">Enter your job offer details.</p>
              </div>
              <button type="button" onClick={() => setShowForm(false)} className="rounded-lg p-2 hover:bg-slate-100">
                <X size={20} />
              </button>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Job title" value={form.title} set={(v) => setForm({ ...form, title: v })} />
              <Field label="Company" value={form.company} set={(v) => setForm({ ...form, company: v })} />
              <Field label="Location" value={form.location} set={(v) => setForm({ ...form, location: v })} />
              <div>
                <label className="text-sm font-semibold">Job type</label>
                <select
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value })}
                  className="mt-2 w-full rounded-lg border p-3 text-sm"
                >
                  <option>Full-time</option>
                  <option>Part-time</option>
                  <option>Contract</option>
                  <option>Internship</option>
                </select>
              </div>
              <Field
                label="Required experience (years)"
                type="number"
                min="0"
                value={form.experience}
                set={(v) => setForm({ ...form, experience: Number(v) })}
              />
            </div>
            <div className="mt-4">
              <Field
                label="Required skills"
                value={form.skills}
                set={(v) => setForm({ ...form, skills: v })}
                placeholder="React, JavaScript, TypeScript"
              />
            </div>
            <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="font-bold text-amber-950">Mandatory eligibility checks</p>
              <p className="mt-1 text-xs text-amber-800">These are pass / fail / verification checks, separate from weighted scoring.</p>
              <div className="mt-3 grid gap-3">
                <Field optional label="Must-have skills" value={form.mustHaveSkills} set={(v) => setForm({ ...form, mustHaveSkills: v })} placeholder="Python, FastAPI" />
                <Field optional label="Required languages" value={form.requiredLanguages} set={(v) => setForm({ ...form, requiredLanguages: v })} placeholder="English" />
                <Field optional label="Required certifications" value={form.requiredCertifications} set={(v) => setForm({ ...form, requiredCertifications: v })} placeholder="AWS Solutions Architect" />
              </div>
            </div>
            <label className="mt-4 block text-sm font-semibold">Job description</label>
            <textarea
              required
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows="4"
              className="mt-2 w-full rounded-lg border p-3 text-sm"
            />
            <WeightEditor
              weights={form.scoring_weights}
              setWeights={(scoring_weights) => setForm({ ...form, scoring_weights })}
            />
            <div className="mt-6 flex justify-end gap-3">
              <button type="button" onClick={() => setShowForm(false)} className="rounded-lg border px-5 py-2.5 font-semibold">
                Cancel
              </button>
              <button
                disabled={weightTotal !== 100}
                className="rounded-lg bg-blue-600 px-5 py-2.5 font-bold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                Publish Job
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Evidence Drill Down Modal */}
      {selectedSkillDrillDown && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="text-emerald-600" size={22} />
                <h3 className="text-lg font-bold text-slate-900">
                  Skill Evidence: {selectedSkillDrillDown.skill || selectedSkillDrillDown.name}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedSkillDrillDown(null)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={20} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-center">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-[10px] font-bold uppercase text-slate-500">Status</p>
                <p className="mt-1 text-xs font-extrabold capitalize text-slate-800">
                  {selectedSkillDrillDown.status?.replaceAll('_', ' ') || 'Verified'}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-[10px] font-bold uppercase text-slate-500">Confidence</p>
                <p className="mt-1 text-xs font-extrabold text-indigo-700">
                  {Math.round((selectedSkillDrillDown.confidence || 1) * 100)}%
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-[10px] font-bold uppercase text-slate-500">Repositories</p>
                <p className="mt-1 text-xs font-extrabold text-slate-800">
                  {selectedSkillDrillDown.repositories?.length || selectedSkillDrillDown.repo_count || 1}
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-[10px] font-bold uppercase text-slate-500">Total Commits</p>
                <p className="mt-1 text-xs font-extrabold text-slate-800">
                  {selectedSkillDrillDown.commit_count || selectedSkillDrillDown.commits || '—'}
                </p>
              </div>
            </div>

            {selectedSkillDrillDown.findings && selectedSkillDrillDown.findings.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500">Verified Findings</h4>
                <div className="space-y-2">
                  {selectedSkillDrillDown.findings.map((f, i) => (
                    <div key={i} className="rounded-xl border border-slate-200 bg-slate-50/70 p-3 text-xs space-y-1">
                      <div className="flex items-center justify-between font-bold text-slate-900">
                        <span className="flex items-center gap-1.5">
                          <FolderGit2 size={14} className="text-indigo-600" /> {f.repository}
                        </span>
                        <span className="text-slate-500 font-mono text-[11px]">{f.file_path || 'Repository root'}</span>
                      </div>
                      <p className="text-slate-600 mt-1">
                        <span className="font-semibold text-slate-700">Matched via:</span> {f.match_type || 'code / package marker'} ({f.detail || 'Verified in repository files'})
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedSkillDrillDown.repositories && selectedSkillDrillDown.repositories.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2">Attributed Repositories</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedSkillDrillDown.repositories.map((r, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center gap-1 rounded-lg bg-indigo-50 border border-indigo-200 px-2.5 py-1 text-xs font-semibold text-indigo-800"
                    >
                      <FolderGit2 size={13} /> {r}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="flex justify-end pt-3 border-t">
              <button
                type="button"
                onClick={() => setSelectedSkillDrillDown(null)}
                className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Snapshot History Modal */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <History className="text-indigo-600" size={22} />
                <div>
                  <h3 className="text-lg font-bold text-slate-900">GitHub Evidence Snapshot Timeline</h3>
                  <p className="text-xs text-slate-500">Immutable historical evidence record</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowHistoryModal(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-3">
              {candidateSnapshots.map((snap) => (
                <div
                  key={snap.snapshot_id}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs space-y-2 hover:border-indigo-300 transition"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-indigo-700">{snap.snapshot_id}</span>
                    <span className="text-slate-500">
                      {snap.verified_at ? new Date(snap.verified_at).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 py-1 text-slate-700 font-semibold">
                    <div>Repositories: {snap.repositories_count || snap.analysis?.repository_count || 0}</div>
                    <div>Commits: {snap.total_commits || snap.analysis?.candidate_commits_sampled || 0}</div>
                    <div>Verified Skills: {snap.verified_skills_count || snap.verified_skills?.length || 0}</div>
                  </div>
                  {snap.verified_skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {snap.verified_skills.map((s, i) => (
                        <span
                          key={i}
                          className="rounded-md bg-white border border-slate-200 px-2 py-0.5 text-[11px] font-medium text-slate-700"
                        >
                          {typeof s === 'string' ? s : s.skill}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {!candidateSnapshots.length && (
                <p className="text-sm text-slate-500 text-center py-6">No historical snapshots recorded yet.</p>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t">
              <button
                type="button"
                onClick={() => setShowHistoryModal(false)}
                className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Snapshot Comparison Modal */}
      {showCompareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <GitCompare className="text-indigo-600" size={22} />
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Compare GitHub Snapshots</h3>
                  <p className="text-xs text-slate-500">Detect growth, new skills, and repository evolution</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowCompareModal(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={20} />
              </button>
            </div>

            {/* Selectors */}
            <div className="grid gap-3 sm:grid-cols-2 bg-slate-50 p-3.5 rounded-xl border border-slate-200">
              <div>
                <label className="text-xs font-bold text-slate-700 uppercase">From Snapshot (Older)</label>
                <select
                  value={compareFromId}
                  onChange={(e) => {
                    setCompareFromId(e.target.value);
                    runCompare(e.target.value, compareToId);
                  }}
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-white p-2 text-xs font-mono"
                >
                  {candidateSnapshots.map((s) => (
                    <option key={s.snapshot_id} value={s.snapshot_id}>
                      {s.snapshot_id} ({new Date(s.verified_at).toLocaleDateString()})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-bold text-slate-700 uppercase">To Snapshot (Newer)</label>
                <select
                  value={compareToId}
                  onChange={(e) => {
                    setCompareToId(e.target.value);
                    runCompare(compareFromId, e.target.value);
                  }}
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-white p-2 text-xs font-mono"
                >
                  {candidateSnapshots.map((s) => (
                    <option key={s.snapshot_id} value={s.snapshot_id}>
                      {s.snapshot_id} ({new Date(s.verified_at).toLocaleDateString()})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {compareData ? (
              <div className="space-y-4 text-xs">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[10px] uppercase font-bold text-slate-500">Commit Delta</p>
                    <p className="text-sm font-bold text-emerald-700">
                      {compareData.commit_growth >= 0 ? `+${compareData.commit_growth}` : compareData.commit_growth}
                    </p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[10px] uppercase font-bold text-slate-500">New Repos</p>
                    <p className="text-sm font-bold text-indigo-700">
                      +{compareData.new_repositories?.length || 0}
                    </p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[10px] uppercase font-bold text-slate-500">New Skills</p>
                    <p className="text-sm font-bold text-emerald-700">
                      +{compareData.newly_verified_skills?.length || 0}
                    </p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[10px] uppercase font-bold text-slate-500">Consistency Δ</p>
                    <p className="text-sm font-bold text-slate-800">
                      {compareData.consistency_delta >= 0
                        ? `+${compareData.consistency_delta}%`
                        : `${compareData.consistency_delta}%`}
                    </p>
                  </div>
                </div>

                {compareData.newly_verified_skills?.length > 0 && (
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-3.5 space-y-1.5">
                    <p className="font-bold text-emerald-900 uppercase text-[11px]">Newly Verified Skills</p>
                    <div className="flex flex-wrap gap-1.5">
                      {compareData.newly_verified_skills.map((s, i) => (
                        <span
                          key={i}
                          className="rounded-md bg-white border border-emerald-300 px-2 py-0.5 font-bold text-emerald-800"
                        >
                          +{s}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {compareData.new_repositories?.length > 0 && (
                  <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-3.5 space-y-1.5">
                    <p className="font-bold text-indigo-900 uppercase text-[11px]">New Repositories Added</p>
                    <div className="flex flex-wrap gap-1.5">
                      {compareData.new_repositories.map((r, i) => (
                        <span
                          key={i}
                          className="rounded-md bg-white border border-indigo-300 px-2 py-0.5 font-bold text-indigo-800"
                        >
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-4">Select two different snapshots to compare differences.</p>
            )}

            <div className="flex justify-end pt-3 border-t">
              <button
                type="button"
                onClick={() => setShowCompareModal(false)}
                className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Evaluation History Modal */}
      {showEvaluationHistoryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="text-indigo-600" size={22} />
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Application Evaluation Audit History</h3>
                  <p className="text-xs text-slate-500">Versioned evaluations and score trajectory</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowEvaluationHistoryModal(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={20} />
              </button>
            </div>

            <div className="space-y-3">
              {evaluationHistory.map((ev, index) => (
                <div
                  key={ev.id || index}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-indigo-600 px-2.5 py-0.5 text-xs font-bold text-white">
                        v{ev.evaluation_version || 1}
                      </span>
                      <span className="font-bold text-slate-900">Score: {ev.score}%</span>
                    </div>
                    <span className="text-slate-500">
                      {ev.evaluated_at ? new Date(ev.evaluated_at).toLocaleString() : 'Initial submission'}
                    </span>
                  </div>
                  <p className="text-slate-600">
                    <span className="font-semibold text-slate-700">Linked Snapshot:</span>{' '}
                    <span className="font-mono text-indigo-700">{ev.github_snapshot_id || 'Initial'}</span>
                  </p>
                  {ev.rationale && <p className="text-slate-600 italic">"{ev.rationale}"</p>}
                </div>
              ))}
              {!evaluationHistory.length && (
                <p className="text-sm text-slate-500 text-center py-6">No prior evaluation versions recorded.</p>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t">
              <button
                type="button"
                onClick={() => setShowEvaluationHistoryModal(false)}
                className="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// COMPONENT: DetailedGithubEvidenceSection
// Renders comprehensive GitHub verification metrics:
// - Verification badge and quality score
// - Job-relevant repositories identified by AI
// - Detected technical skills with confidence and file-level evidence markers
// - Language distribution percentages
// ============================================================================
function DetailedGithubEvidenceSection({
  evidence,
  snapshots = [],
  onOpenSkillDrillDown,
  onOpenHistory,
  onOpenCompare,
}) {
  if (!evidence) return null;
  const isVerified = evidence.verification_status === 'verified';
  const analysis = evidence.analysis || {};
  const qualityScore = analysis.code_quality_score
    ?? (evidence.repositories?.length
      ? Math.round(
        evidence.repositories.reduce((total, repo) => total + Number(repo.code_quality?.score || 0), 0)
        / evidence.repositories.length,
      )
      : 0);
  const geminiAnalysis = evidence.gemini_analysis || {};
  const jobRepos = evidence.job_relevant_repositories || [];
  const skillEvidenceList = evidence.skill_evidence || [];

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white shadow-sm">
            <Github size={22} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-base text-slate-900">Verified GitHub Technical Profile</h3>
              <span
                className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold ${
                  isVerified
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                }`}
              >
                {isVerified ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
                {evidence.verification_status?.replaceAll('_', ' ')}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
              <span>@{evidence.username || 'github-user'}</span>
              <span>·</span>
              <span>Snapshot: <span className="font-mono text-indigo-700">{evidence.snapshot_id || 'current'}</span></span>
              {evidence.verified_at && (
                <>
                  <span>·</span>
                  <span>{new Date(evidence.verified_at).toLocaleDateString()}</span>
                </>
              )}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {evidence.github_url && (
            <a
              href={evidence.github_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
            >
              <ExternalLink size={13} /> Profile
            </a>
          )}
          <button
            type="button"
            onClick={onOpenHistory}
            className="flex items-center gap-1 rounded-lg border border-indigo-200 bg-indigo-50/50 px-3 py-1.5 text-xs font-bold text-indigo-700 hover:bg-indigo-100"
          >
            <History size={13} /> History ({snapshots.length})
          </button>
          {snapshots.length >= 2 && (
            <button
              type="button"
              onClick={onOpenCompare}
              className="flex items-center gap-1 rounded-lg border border-purple-200 bg-purple-50/50 px-3 py-1.5 text-xs font-bold text-purple-700 hover:bg-purple-100"
            >
              <GitCompare size={13} /> Compare
            </button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricCard label="Repositories" value={analysis.repository_count || 0} icon={<FolderGit2 size={16} />} />
        <MetricCard label="With Tests" value={analysis.tested_repository_count || 0} icon={<CheckCircle size={16} />} />
        <MetricCard label="Commits Sampled" value={analysis.candidate_commits_sampled || 0} icon={<GitBranch size={16} />} />
        <MetricCard
          label="Code Quality"
          value={`${qualityScore}/100`}
          icon={<ShieldCheck size={16} />}
        />
      </div>

      {/* Verified Skills & Interactive Drill Down */}
      {skillEvidenceList.length > 0 && (
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2.5">
            Verified Skill Attributions (Click to Drill Down)
          </h4>
          <div className="flex flex-wrap gap-2">
            {skillEvidenceList.map((sk, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onOpenSkillDrillDown(sk)}
                className="group flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50/70 px-3 py-1.5 text-xs font-semibold text-emerald-800 hover:bg-emerald-100 transition shadow-sm"
              >
                <CheckCircle2 size={13} className="text-emerald-600" />
                <span>{sk.skill}</span>
                <span className="rounded bg-white px-1.5 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                  {Math.round((sk.confidence || 1) * 100)}%
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Gemini GitHub Analysis */}
      {geminiAnalysis && (geminiAnalysis.frameworks_detected?.length > 0 || geminiAnalysis.technical_relevance_summary) && (
        <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4 space-y-2 text-xs">
          <p className="font-bold text-slate-700 uppercase text-[11px] flex items-center gap-1.5">
            <Sparkles size={14} className="text-indigo-600" /> Gemini Repository & Code Analysis
          </p>
          {geminiAnalysis.technical_relevance_summary && (
            <p className="text-slate-600 leading-relaxed">{geminiAnalysis.technical_relevance_summary}</p>
          )}
          {geminiAnalysis.frameworks_detected?.length > 0 && (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {geminiAnalysis.frameworks_detected.map((fw, i) => (
                <span
                  key={i}
                  className="rounded-md bg-white border border-slate-200 px-2 py-0.5 text-[11px] font-medium text-slate-700"
                >
                  {fw}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Job Relevant Repositories */}
      {jobRepos.length > 0 && (
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wide text-slate-500 mb-2.5">
            Job-Relevant Repositories ({jobRepos.length})
          </h4>
          <div className="grid gap-2 sm:grid-cols-2">
            {jobRepos.map((repo, idx) => (
              <div
                key={idx}
                className="rounded-xl border border-slate-200 bg-white p-3 text-xs space-y-1 hover:border-slate-300 transition"
              >
                <div className="flex items-center justify-between font-bold text-slate-900">
                  <span className="flex items-center gap-1.5">
                    <FolderGit2 size={14} className="text-indigo-600" /> {repo.name}
                  </span>
                  <span className="text-[11px] font-bold text-indigo-700">
                    Relevance: {Math.round((repo.relevance_score || 0) * 100)}%
                  </span>
                </div>
                <p className="text-slate-500 text-[11px] line-clamp-1">{repo.description || 'No repository description'}</p>
                <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] text-slate-500">
                  {repo.primary_language && <span>Lang: {repo.primary_language}</span>}
                  <span>Commits: {repo.commit_count || 0}</span>
                  {repo.has_tests && <span className="text-emerald-700 font-semibold">✓ Tests</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Languages breakdown */}
      {analysis.main_languages?.length > 0 && (
        <div className="pt-2 border-t">
          <p className="text-xs font-bold uppercase text-slate-500 mb-2">Language Distribution</p>
          <TagList
            items={analysis.main_languages.slice(0, 8).map((item) => `${item.name} ${item.percentage}%`)}
            tone="green"
          />
        </div>
      )}
    </section>
  );
}

function MetricCard({ label, value, icon }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 shadow-sm">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white text-indigo-600 border border-slate-200 shadow-xs">
        {icon}
      </div>
      <div>
        <p className="text-[10px] font-bold uppercase text-slate-500">{label}</p>
        <p className="mt-0.5 text-sm font-extrabold text-slate-900">{value}</p>
      </div>
    </div>
  );
}

// ============================================================================
// COMPONENT: ScoreOverrides
// Recruiter Score Adjustments & Human Decision Panel:
// - Displays AI-assisted multi-dimensional score breakdown
// - Allows recording external technical assessment percentages
// - Allows recruiters to override a score category with an audit reason
// - Logs final human hiring decision (Shortlist, Offer, Hold, Reject)
// ============================================================================
function ScoreOverrides({ application, token }) {
  const [assessment, setAssessment] = useState(null);
  const [category, setCategory] = useState('technical_skills');
  const [score, setScore] = useState('');
  const [reason, setReason] = useState('');
  const [message, setMessage] = useState('');
  const [technicalScore, setTechnicalScore] = useState('');
  const [decision, setDecision] = useState('Shortlist');
  const [decisionReason, setDecisionReason] = useState('');

  const load = () =>
    apiRequest(`/api/applications/${application.id}/assessment?token=${encodeURIComponent(token)}`)
      .then(setAssessment)
      .catch((error) => setMessage(error.message));

  useEffect(() => {
    load();
  }, [application.id]);

  const categories = assessment?.ai_evaluation?.scores || application.scores || {};
  const selected = categories[category] || {};

  const submit = async (event) => {
    event.preventDefault();
    setMessage('');
    try {
      await apiRequest(`/api/applications/${application.id}/overrides?token=${encodeURIComponent(token)}`, {
        method: 'POST',
        body: JSON.stringify({ category, recruiter_score: Number(score), override_reason: reason }),
      });
      setScore('');
      setReason('');
      setMessage('Override saved with audit history.');
      load();
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <section className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm space-y-5">
      {assessment && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <p className="text-xs font-bold uppercase text-indigo-600">AI-Assisted Match Assessment</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Eligibility" value={`${assessment.eligibility?.summary?.met || 0}/${assessment.eligibility?.summary?.total || 0} met`} icon={<ShieldCheck size={18} />} />
            <MetricCard label="Profile" value={`${assessment.profile?.score || 0}/${assessment.profile?.maximum || 70}`} icon={<User size={18} />} />
            <MetricCard label="Technical" value={assessment.technical_assessment?.status === 'completed' ? `${assessment.technical_assessment.weighted_score}/${assessment.technical_assessment.max_score}` : 'Pending'} icon={<Code size={18} />} />
            <MetricCard label="Interview" value={assessment.structured_interview?.status === 'completed' ? `${assessment.structured_interview.weighted_score}/${assessment.structured_interview.max_score}` : 'Pending'} icon={<Briefcase size={18} />} />
          </div>
          <p className="mt-3 text-sm font-bold text-slate-800">{assessment.match_assessment} {assessment.final_score != null ? `· ${assessment.final_score}/100` : '· profile stage only'}</p>
          <p className="mt-1 text-xs text-slate-500">{assessment.disclaimer}</p>
        </div>
      )}
      <form className="flex flex-wrap items-end gap-3" onSubmit={async (event) => { event.preventDefault(); await apiRequest(`/api/applications/${application.id}/technical-assessments?token=${encodeURIComponent(token)}`, { method: 'POST', body: JSON.stringify({ raw_score: Number(technicalScore), assessment_type: 'technical assessment' }) }); setTechnicalScore(''); load(); }}>
        <label className="text-xs font-semibold text-amber-900">Technical assessment %<input required type="number" min="0" max="100" value={technicalScore} onChange={(e) => setTechnicalScore(e.target.value)} className="mt-1 block rounded-lg border border-amber-300 bg-white p-2" /></label>
        <button className="rounded-lg bg-indigo-700 px-4 py-2 text-sm font-bold text-white">Record assessment</button>
      </form>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-bold text-amber-950">Recruiter score overrides</h3>
          <p className="mt-1 text-xs text-amber-800">Adjust one category only with a documented evidence-based reason.</p>
        </div>
        {assessment && (
          <span className="rounded-full bg-white px-3 py-1 text-sm font-extrabold text-amber-800">
            Effective {assessment.pre_interview_score}/100
          </span>
        )}
      </div>
      <form onSubmit={submit} className="mt-4 grid gap-3 md:grid-cols-[1fr_120px_2fr_auto]">
        <select
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setScore('');
          }}
          className="rounded-lg border border-amber-300 bg-white p-2.5 text-sm"
        >
          {Object.keys(categories)
            .filter((key) => key !== 'interview')
            .map((key) => (
              <option key={key} value={key}>
                {key.replaceAll('_', ' ')}
              </option>
            ))}
        </select>
        <input
          required
          type="number"
          min="0"
          max={selected.maximum_score ?? 0}
          step="0.01"
          value={score}
          onChange={(e) => setScore(e.target.value)}
          placeholder={`0–${selected.maximum_score ?? 0}`}
          className="rounded-lg border border-amber-300 bg-white p-2.5 text-sm"
        />
        <input
          required
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Evidence-based override reason"
          className="rounded-lg border border-amber-300 bg-white p-2.5 text-sm"
        />
        <button className="rounded-lg bg-amber-700 px-4 py-2 text-sm font-bold text-white">Save</button>
      </form>
      {assessment?.overrides?.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {assessment.overrides.map((item) => (
            <span
              key={item.id}
              title={item.override_reason}
              className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-amber-900 ring-1 ring-amber-200"
            >
              {item.category.replaceAll('_', ' ')}: {item.recruiter_score}/
              {categories[item.category]?.maximum_score || 0}
            </span>
          ))}
        </div>
      )}
      {message && <p className="mt-3 text-sm font-semibold text-amber-900">{message}</p>}
      <form className="grid gap-3 border-t border-amber-200 pt-4 sm:grid-cols-[180px_1fr_auto]" onSubmit={async (event) => { event.preventDefault(); await apiRequest(`/api/applications/${application.id}/decision?token=${encodeURIComponent(token)}`, { method: 'POST', body: JSON.stringify({ decision, reason: decisionReason }) }); setDecisionReason(''); load(); }}>
        <select value={decision} onChange={(e) => setDecision(e.target.value)} className="rounded-lg border border-amber-300 bg-white p-2.5 text-sm">{['Shortlist', 'Technical Interview', 'Final Interview', 'Offer', 'Hold', 'Reject'].map((x) => <option key={x}>{x}</option>)}</select>
        <input required value={decisionReason} onChange={(e) => setDecisionReason(e.target.value)} placeholder="Human decision reason" className="rounded-lg border border-amber-300 bg-white p-2.5 text-sm" />
        <button className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-bold text-white">Save human decision</button>
      </form>
    </section>
  );
}

// ============================================================================
// COMPONENT: WeightEditor
// Allows recruiter to customize scoring weights per category (Total must be 100%)
// Categories: Skills, Experience, Projects, Education, GitHub, Interviews, etc.
// ============================================================================
function WeightEditor({ weights, setWeights }) {
  const labels = {
    technical_skills: 'Technical Skills',
    experience: 'Experience',
    projects: 'Projects',
    education: 'Education',
    certifications: 'Certifications',
    github_evidence: 'GitHub Evidence',
    job_relevance: 'Job Relevance',
    technical_assessment: 'Technical Assessment',
    structured_interview: 'Structured Interview',
  };
  const total = Object.values(weights || {}).reduce((sum, value) => sum + Number(value || 0), 0);
  return (
    <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-bold text-slate-900">Scoring allocation</p>
          <p className="text-xs text-slate-500">Set job-specific maximum marks.</p>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-sm font-extrabold ${
            total === 100 ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-800'
          }`}
        >
          {total} / 100
        </span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {Object.entries(labels).map(([key, label]) => (
          <label key={key} className="text-xs font-semibold text-slate-600">
            {label}
            <input
              type="number"
              min="0"
              max="100"
              value={weights?.[key] ?? 0}
              onChange={(e) => setWeights({ ...weights, [key]: Math.max(0, Number(e.target.value)) })}
              className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            />
          </label>
        ))}
      </div>
      <p className={`mt-3 text-sm font-semibold ${total === 100 ? 'text-green-700' : 'text-amber-700'}`}>
        {total === 100 ? 'Ready to publish.' : total < 100 ? `${100 - total} marks remaining.` : `Reduce the allocation by ${total - 100} marks.`}
      </p>
    </div>
  );
}

// Reusable text / number form input field
function Field({ label, value, set, placeholder, type = 'text', min, optional = false }) {
  return (
    <div>
      <label className="text-sm font-semibold">{label}</label>
      <input
        type={type}
        min={min}
        required={!optional}
        value={value}
        onChange={(e) => set(e.target.value)}
        placeholder={placeholder}
        className="mt-2 w-full rounded-lg border p-3 text-sm outline-none focus:border-blue-500"
      />
    </div>
  );
}

function Score({ label, value, good = false }) {
  return (
    <div className={`rounded-lg p-3 ${good ? 'bg-green-50' : 'bg-red-50'}`}>
      <p className={`text-xs font-bold uppercase ${good ? 'text-green-700' : 'text-red-700'}`}>{label}</p>
      <p className={`mt-1 text-xl font-extrabold ${good ? 'text-green-700' : 'text-red-700'}`}>
        {Number(value || 0)}%
      </p>
    </div>
  );
}

function DetailPanel({ title, children }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h4 className="mb-3 text-xs font-bold uppercase text-slate-500">{title}</h4>
      {children}
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <p className="mb-2 text-sm text-slate-600">
      <span className="font-semibold text-slate-800">{label}:</span> {value || 'Not provided'}
    </p>
  );
}

// Reusable badge tag list with color tones (green for matched, red for missing, amber for partial)
function TagList({ items, tone }) {
  const styles = { green: 'bg-green-50 text-green-700', red: 'bg-red-50 text-red-700', amber: 'bg-amber-50 text-amber-700' };
  return (
    <div className="mb-3 flex flex-wrap gap-2">
      {items.map((item) => (
        <span key={item} className={`rounded-full px-2.5 py-1 text-xs font-semibold ${styles[tone]}`}>
          {item}
        </span>
      ))}
    </div>
  );
}

// Action button for updating application status (Shortlist, Hire, Reject)
function StatusButton({ active, color, onClick, icon, children }) {
  const styles = {
    green: active ? 'bg-green-600 text-white' : 'border-green-200 bg-white text-green-700',
    amber: active ? 'bg-amber-500 text-white' : 'border-amber-200 bg-white text-amber-700',
    red: active ? 'bg-red-600 text-white' : 'border-red-200 bg-white text-red-700',
  };
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-bold ${styles[color]}`}
    >
      {icon}
      {children}
    </button>
  );
}

// Card displaying structured recruiter guidance (Strengths, Risks, Interview Focus)
function GuidanceItem({ label, value }) {
  return (
    <div className="rounded-lg border border-indigo-100 bg-white p-4">
      <p className="text-xs font-bold uppercase text-indigo-600">{label}</p>
      <p className="mt-2 text-sm leading-6 text-slate-700">{value || 'Not available for this application.'}</p>
    </div>
  );
}

// ============================================================================
// HELPER: recruiterReviewText
// Generates a human-readable AI recommendation summary for a candidate:
// Formulates candidate fit level (Strong/Good/Moderate/Weak), verified strengths,
// evidence gaps, and interview suggestions emphasizing human-in-the-loop hiring.
// ============================================================================
function recruiterReviewText(application) {
  const guidance = application.analysis?.recruiter_guidance;
  if (guidance) {
    return `AI-assisted match assessment: ${guidance.reason} Verified strengths: ${guidance.strengths}. Evidence gaps: ${guidance.risks}. Suggested validation: ${guidance.interview_focus}. A human makes the final hiring decision.`;
  }
  const score = Number(application.score || 0);
  const recommendation = score >= 85 ? 'Strong Match' : score >= 70 ? 'Good Match' : score >= 55 ? 'Moderate Match' : 'Weak Match';
  const matched = application.analysis?.matched_skills?.join(', ') || 'no verified required skills';
  const missing = application.analysis?.missing_skills?.join(', ') || 'no major skill gaps';
  return `AI-assisted match assessment: ${recommendation}. The candidate has a ${score}% evidence-based fit for this job. Verified strengths: ${matched}. Evidence gaps: ${missing}. Validate these areas in a structured interview or practical assessment; a human makes the final hiring decision.`;
}
