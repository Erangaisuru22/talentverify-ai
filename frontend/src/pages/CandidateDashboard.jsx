/**
 * @file CandidateDashboard.jsx
 * @description Candidate dashboard view facilitating job discovery, AI CV parsing (Gemini),
 * real-time role compatibility analysis, profile skill management, and application lifecycle tracking.
 */

import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, Briefcase, CheckCircle, Clock3, FileText, Loader2, MapPin, Search, Target, Upload, X } from 'lucide-react';
import { apiForm, apiRequest } from '../services/api';

/**
 * Main dashboard component for candidates.
 *
 * @param {Object} props
 * @param {Array} [props.jobs=[]] - Available job postings.
 * @param {Object} props.user - Current candidate user profile.
 * @param {string} props.token - Active authentication session token.
 * @param {Array} [props.applications=[]] - Candidate's submitted applications.
 * @param {(profile: Object) => Promise<any>} props.onSaveProfile - Callback to persist candidate profile changes.
 * @param {(app: Object) => Promise<any>} props.onApply - Callback to submit a job application.
 * @param {(appId: string|number) => Promise<any>} props.onWithdraw - Callback to withdraw an application.
 * @param {() => void} [props.onNavigateProfile] - Navigation helper to jump to Profile view.
 */
export default function CandidateDashboard({ jobs = [], user, token, applications = [], onSaveProfile, onApply, onWithdraw, onNavigateProfile }) {
  // --- DOM References ---
  const fileInputRef = useRef(null);
  const applicationsRef = useRef(null);

  // --- Component States ---
  const [selectedJobId, setSelectedJobId] = useState(jobs[0]?.id || null);
  const [cvText, setCvText] = useState('');                 // Extracted raw text from uploaded CV
  const [fileName, setFileName] = useState('');             // Name of uploaded CV file
  const [importing, setImporting] = useState(false);         // CV uploading & parsing loading state
  const [loading, setLoading] = useState(false);             // Compatibility analysis in-progress flag
  const [message, setMessage] = useState('');               // Success notice message
  const [error, setError] = useState('');                   // Error notice message
  const [result, setResult] = useState(null);               // Gemini AI compatibility analysis result
  const [searchDraft, setSearchDraft] = useState('');       // Search input buffer
  const [searchQuery, setSearchQuery] = useState('');       // Submitted job search query
  const [applied, setApplied] = useState(false);             // Immediate application submission flag
  const [alreadyAppliedModal, setAlreadyAppliedModal] = useState(false); // Modal trigger for duplicate applications
  const [noSkillsModal, setNoSkillsModal] = useState(false); // Modal trigger when candidate has no profile skills

  // Selected job object and skills requirements
  const selectedJob = jobs.find((job) => job.id === selectedJobId) || jobs[0];
  const hasProfileSkills = Boolean(
    String(user?.technicalSkills || '').trim() ||
    String(user?.softSkills || '').trim() ||
    String(user?.skills || '').trim() ||
    Boolean(cvText)
  );
  const jobSkills = selectedJob?.skills || 'React, JavaScript, Tailwind, TypeScript, Next.js';

  // Filtered job list based on candidate search query
  const filteredJobs = jobs.filter((job) => {
    const query = searchQuery.trim().toLowerCase();
    return !query || [job.title, job.company, job.location, job.type, job.skills].some((value) => String(value || '').toLowerCase().includes(query));
  });

  // Check if candidate has an existing active application for the currently selected job
  const existingApplication = applications.find((item) => item.jobId === selectedJob?.id && !['Withdrawn', 'Application Withdrawn'].includes(item.status));

  // Reset applied state when active job selection changes or has no application
  useEffect(() => {
    if (!existingApplication) setApplied(false);
  }, [existingApplication]);

  /**
   * Helper to merge existing skill strings with newly extracted skill arrays without duplicates.
   * @param {string} existing - Comma-separated existing skills.
   * @param {Array<string>} extracted - Array of newly discovered skill names.
   * @returns {string} Merged comma-separated skill list.
   */
  const mergeSkills = (existing, extracted) => {
    const merged = [];
    const seen = new Set();
    [...String(existing || '').split(','), ...extracted].forEach((skill) => {
      const clean = String(skill).trim();
      const key = clean.toLowerCase();
      if (clean && !seen.has(key)) { seen.add(key); merged.push(clean); }
    });
    return merged.join(', ');
  };

  /**
   * Uploads and parses candidate CV document (PDF/DOCX/TXT).
   * Automatically invokes Gemini AI to extract technical and soft skills,
   * experience, and updates the candidate's profile in real time.
   * @param {File} file - User selected CV file.
   */
  const handleImport = async (file) => {
    if (!file) return;
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(extension)) { setError('Please choose a PDF, DOCX, or TXT file.'); return; }
    if (file.size > 10 * 1024 * 1024) { setError('CV file must be 10 MB or smaller.'); return; }
    setImporting(true); setError(''); setMessage(''); setResult(null);
    try {
      // Step 1: Upload and extract text content from CV file
      const uploadData = new FormData(); uploadData.append('file', file);
      const imported = await apiForm(`/api/import-cv?token=${encodeURIComponent(token)}`, uploadData);

      // Step 2: Send extracted text to AI for skill and experience extraction
      const analysisData = new FormData();
      analysisData.append('job_title', selectedJob?.title || 'General Candidate Profile');
      analysisData.append('job_skills', jobSkills);
      analysisData.append('cv_text', imported.text);
      analysisData.append('candidate_experience', Number(user.experience || 0));
      analysisData.append('required_experience', Number(selectedJob?.experience || 0));
      const analysis = await apiForm('/api/analyze-cv', analysisData);

      const details = analysis.profile_details || {};
      const extractedTech = details.technical_skills || [];
      const extractedSoft = details.soft_skills || [];
      const extractedSkills = analysis.extracted_skills || [...extractedTech, ...extractedSoft];

      // Merge newly extracted skills with candidate's existing profile skills
      const newTechSkills = mergeSkills(user.technicalSkills || '', extractedTech);
      const newSoftSkills = mergeSkills(user.softSkills || '', extractedSoft);
      const combinedSkills = mergeSkills(user.skills, [...extractedSkills, ...extractedTech, ...extractedSoft]);

      const profileUpdate = {
        technicalSkills: newTechSkills,
        softSkills: newSoftSkills,
        skills: combinedSkills,
        headline: details.headline || user.headline || '',
        phone: details.phone || user.phone || '',
        location: details.location || user.location || '',
        bio: details.bio || user.bio || '',
        experience: Math.max(Number(details.experience || 0), Number(user.experience || 0)),
        cvFileName: imported.filename || file.name,
        cvImportedAt: new Date().toISOString(),
      };

      // Persist merged profile details to backend
      await onSaveProfile(profileUpdate);
      setCvText(imported.text); setFileName(imported.filename || file.name);
      setResult(analysis);
      
      const techCount = extractedTech.length;
      const softCount = extractedSoft.length;
      const totalCount = extractedSkills.length;
      setMessage(`CV analyzed with Gemini: ${techCount > 0 ? `${techCount} Technical & ${softCount} Soft skills` : `${totalCount} skills`} saved to profile.`);
    } catch (err) { setError(err.message || 'CV processing failed. Please check the backend.'); }
    finally { setImporting(false); if (fileInputRef.current) fileInputRef.current.value = ''; }
  };

  /** Candidate profile text compilation for reference */
  const profileText = [
    `Candidate: ${user.name || ''}`,
    `Professional headline: ${user.headline || ''}`,
    `Technical Skills: ${user.technicalSkills || ''}`,
    `Soft Skills: ${user.softSkills || ''}`,
    `Experience: ${user.experience || 0} years`,
    `About: ${user.bio || ''}`,
    `Location: ${user.location || ''}`,
  ].join('\n');

  /**
   * Requests backend candidate evaluation for the selected job.
   * Compares candidate profile and evidence against role requirements.
   */
  const analyze = async () => {
    if (!selectedJob) { setError('Please select a job first.'); return; }
    if (existingApplication || applied) {
      setAlreadyAppliedModal(true);
      setError('You have already applied for this job.');
      return;
    }
    const hasSkills = Boolean(
      String(user?.technicalSkills || '').trim() ||
      String(user?.softSkills || '').trim() ||
      String(user?.skills || '').trim() ||
      Boolean(cvText)
    );
    if (!hasSkills) {
      setResult(null);
      setNoSkillsModal(true);
      setError('Please add and save skills in your profile before running analysis.');
      return;
    }
    setLoading(true); setError('');
    try {
      const analysis = await apiRequest(`/api/jobs/${selectedJob.id}/candidate-evaluation?token=${encodeURIComponent(token)}`, { method: 'POST' });
      setResult(analysis);
    } catch (err) {
      setError(err.message || 'Could not connect to the analysis service.');
    } finally {
      setLoading(false);
    }
  };

  /** Smoothly scrolls the viewport to the 'My Applications' list */
  const showApplications = () => {
    setAlreadyAppliedModal(false);
    setTimeout(() => applicationsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 0);
  };


  /**
   * Submits the candidate's application with AI compatibility snapshot and scores.
   */
  const confirmApplication = async () => {
    if (!selectedJob || !result || existingApplication) return;
    setLoading(true); setError('');
    try {
      await onApply({
        jobId: selectedJob.id, jobTitle: selectedJob.title, company: selectedJob.company, location: selectedJob.location,
        score: result.score, matchedSkills: result.matched_skills || [],
        requiredSkills: jobSkills.split(',').map((skill) => skill.trim()).filter(Boolean),
        requiredExperience: Number(selectedJob.experience || 0), candidateExperience: Number(user.experience || 0), analysis: result,
        candidateSnapshot: { name: user.name || '', headline: user.headline || '', phone: user.phone || '', location: user.location || '',
          skills: [user.technicalSkills, user.softSkills].filter(Boolean).join(', '), technicalSkills: user.technicalSkills || '',
          softSkills: user.softSkills || '', experience: Number(user.experience || 0), cvFileName: fileName || user.cvFileName || '',
          portfolioUrl: user.portfolioUrl || '' },
      });
      setApplied(true);
      setTimeout(() => applicationsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    } catch (err) {
      setApplied(false);
      setError(err.message || 'Application could not be submitted.');
    } finally { setLoading(false); }
  };

  /**
   * Deletes a specific skill from the candidate's profile in the database and updates state.
   * @param {'technicalSkills'|'softSkills'} key - Target skill property.
   * @param {string} skillToRemove - Name of the skill to delete.
   */
  const removeProfileSkill = async (key, skillToRemove) => {
    const existing = user[key] || '';
    const updatedList = existing.split(',').map((s) => s.trim()).filter((s) => s && s.toLowerCase() !== skillToRemove.toLowerCase());
    const updatedStr = updatedList.join(', ');

    const tech = key === 'technicalSkills' ? updatedStr : (user.technicalSkills || '');
    const soft = key === 'softSkills' ? updatedStr : (user.softSkills || '');
    const combined = Array.from(new Set([...tech.split(','), ...soft.split(',')])).map((s) => s.trim()).filter(Boolean).join(', ');

    const kind = key === 'technicalSkills' ? 'technical' : 'soft';
    try {
      await apiRequest(`/api/candidates/me/skills?skill=${encodeURIComponent(skillToRemove)}&kind=${kind}&token=${encodeURIComponent(token)}`, { method: 'DELETE' });
      await onSaveProfile({ [key]: updatedStr, skills: combined });
    } catch (error) { setError(error.message); }
  };

  return <div className="min-w-0 space-y-6 sm:space-y-8">
    {applications.length > 0 && <div className="flex justify-end"><button type="button" onClick={showApplications} className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-bold text-blue-700 hover:bg-blue-100">My Applications ({applications.length})</button></div>}
    {!hasProfileSkills && (
      <div className="rounded-2xl border border-amber-300 bg-amber-50/90 p-5 text-amber-900 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-start sm:items-center gap-3.5">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-100 border border-amber-300 text-amber-700">
            <AlertCircle size={22} />
          </div>
          <div>
            <h4 className="font-bold text-base text-amber-950">Action Required: Missing Profile Skills or CV</h4>
            <p className="text-xs text-amber-800 mt-0.5">
              Please import your CV or add skills to your profile to perform AI job compatibility analysis.
            </p>
          </div>
        </div>
        <div className="flex w-full flex-col gap-2 sm:w-auto sm:shrink-0 sm:flex-row">
          {onNavigateProfile && (
            <button
              onClick={onNavigateProfile}
              className="rounded-xl border border-amber-400 bg-white px-3.5 py-2 text-xs font-bold text-amber-900 hover:bg-amber-100/50 transition shadow-sm"
            >
              ✏️ Go to Profile
            </button>
          )}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center justify-center gap-1.5 rounded-xl bg-amber-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-amber-700 transition shadow-sm"
          >
            <Upload size={14} /> Import CV Now
          </button>
        </div>
      </div>
    )}

    {/* Section: Job Search & Selection Carousel */}
    <section>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><h2 className="text-xl font-bold">Find your next role</h2><p className="mt-1 text-sm text-slate-500">Search by title, company, skill, or location.</p></div><form onSubmit={(event)=>{event.preventDefault();setSearchQuery(searchDraft);}} className="flex w-full max-w-xl gap-2"><div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18}/><input value={searchDraft} onChange={(e)=>setSearchDraft(e.target.value)} placeholder="Search jobs" className="h-11 w-full rounded-lg border border-slate-300 pl-10 pr-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"/></div><button className="h-11 rounded-lg bg-slate-900 px-5 text-sm font-bold text-white hover:bg-slate-800">Search</button></form></div>
      <div className="flex gap-3 overflow-x-auto pb-2">{filteredJobs.map((job) => <button key={job.id} onClick={() => { setSelectedJobId(job.id); setResult(null); setApplied(false); }} className={`min-w-64 rounded-lg border p-4 text-left transition ${selectedJob?.id === job.id ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-100' : 'border-slate-200 bg-white hover:border-slate-300'}`}><p className="font-bold">{job.title}</p><p className="mt-1 text-sm text-slate-500">{job.company} · {job.location}</p><div className="mt-3 flex gap-2"><span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold">{job.type}</span><span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700">{Number(job.experience || 0)}+ yrs</span></div></button>)}{!filteredJobs.length&&<div className="w-full rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">No jobs match “{searchQuery}”.</div>}</div>
    </section>

    {/* Section: Job Details & AI CV Skill Extraction Panel */}
    <div className="grid gap-8 md:grid-cols-2"><div className="rounded-xl border bg-white p-6 shadow-sm">
      <h2 className="text-xl font-bold">{selectedJob?.title || 'Select a job'}</h2><p className="mt-1 text-slate-500">{selectedJob ? `${selectedJob.company} · ${selectedJob.location}` : 'No available job selected'}</p><p className="mt-3 text-sm font-semibold text-slate-700">Experience: {Number(selectedJob?.experience || 0)}+ years required <span className="font-normal text-slate-400">· You have {Number(user.experience || 0)} years</span></p>
      {selectedJob?.description&&<p className="mt-4 text-sm leading-6 text-slate-600">{selectedJob.description}</p>}
      <div className="my-6"><h3 className="mb-2 text-sm font-semibold">Required Skills</h3><div className="flex flex-wrap gap-2">{jobSkills.split(',').map((skill)=><span key={skill} className="rounded-full bg-slate-100 px-2 py-1 text-xs">{skill.trim()}</span>)}</div></div>
      <div className="border-t pt-6"><div className="mb-2 flex items-center justify-between"><label className="text-sm font-semibold">CV upload <span className="font-normal text-slate-400">(optional)</span></label><span className="text-xs text-slate-400">Profile is used without a CV</span></div>
        <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={(e)=>handleImport(e.target.files?.[0])}/>
        <button type="button" disabled={importing} onClick={()=>fileInputRef.current?.click()} onDragOver={(e)=>e.preventDefault()} onDrop={(e)=>{e.preventDefault();handleImport(e.dataTransfer.files?.[0]);}} className="w-full rounded-xl border-2 border-dashed border-blue-200 bg-blue-50/60 p-6 disabled:opacity-60">{importing?<Loader2 className="mx-auto mb-2 animate-spin text-blue-600"/>:<Upload className="mx-auto mb-2 text-blue-600"/>}<p className="text-sm font-bold">{importing?'Gemini AI is analyzing & extracting skills...':'Drop CV or click to browse'}</p><p className="mt-1 text-xs text-slate-500">PDF, DOCX or TXT · Max 10 MB</p></button>
        {fileName&&<div className="mt-3 flex items-center gap-2 rounded-lg bg-green-50 p-3 text-sm text-green-800"><FileText size={18}/><span className="flex-1 truncate font-semibold">{fileName}</span><button onClick={()=>{setFileName('');setCvText('');setResult(null);}}><X size={16}/></button></div>}
        {message&&<p className="mt-3 flex items-center gap-2 text-sm font-semibold text-green-600"><CheckCircle size={17}/>{message}</p>}{error&&<p role="alert" className="mt-3 rounded-lg bg-red-50 p-3 text-sm font-medium text-red-700">{error}</p>}

        {(user.technicalSkills || user.softSkills) && (
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50/80 p-4 space-y-3">
            <p className="text-xs font-bold uppercase text-slate-600">Saved Profile Skills (Gemini Extracted from your cv)</p>
            {user.technicalSkills && (
              <div>
                <p className="text-[11px] font-semibold text-indigo-600 uppercase">Technical Skills</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {user.technicalSkills.split(',').map((s, i) => {
                    const skill = s.trim();
                    if (!skill) return null;
                    return (
                      <span key={i} className="inline-flex items-center gap-1 rounded-md bg-indigo-100/70 border border-indigo-200 px-2 py-0.5 text-xs font-medium text-indigo-800">
                        {skill}
                        <button
                          type="button"
                          onClick={() => removeProfileSkill('technicalSkills', skill)}
                          className="text-indigo-400 hover:text-red-600 rounded p-0.5 transition"
                          title={`Remove ${skill}`}
                        >
                          <X size={11} />
                        </button>
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
            {user.softSkills && (
              <div>
                <p className="text-[11px] font-semibold text-emerald-600 uppercase">Soft Skills</p>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {user.softSkills.split(',').map((s, i) => {
                    const skill = s.trim();
                    if (!skill) return null;
                    return (
                      <span key={i} className="inline-flex items-center gap-1 rounded-md bg-emerald-100/70 border border-emerald-200 px-2 py-0.5 text-xs font-medium text-emerald-800">
                        {skill}
                        <button
                          type="button"
                          onClick={() => removeProfileSkill('softSkills', skill)}
                          className="text-emerald-400 hover:text-red-600 rounded p-0.5 transition"
                          title={`Remove ${skill}`}
                        >
                          <X size={11} />
                        </button>
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        <button onClick={analyze} disabled={loading||importing||!selectedJob} className={`mt-5 flex w-full items-center justify-center gap-2 rounded-lg py-3 font-bold text-white transition ${existingApplication || applied ? 'bg-amber-600 hover:bg-amber-700' : 'bg-blue-600 hover:bg-blue-700'}`}>{loading?<><Loader2 className="animate-spin" size={18}/>Analyzing with Gemini...</>:existingApplication || applied ? 'Already Applied' : 'Analyze & Apply'}</button>
      </div>
    </div>

    {/* Section: AI Compatibility Report Results */}
    {hasProfileSkills && result && !existingApplication && !applied ? <div className="relative overflow-hidden rounded-xl border bg-white p-6 shadow-sm">
      <div className="absolute inset-x-0 top-0 h-1 bg-blue-600"/>
      <h3 className="mb-6 flex items-center gap-2 text-lg font-bold"><span className="rounded-lg bg-blue-100 p-1.5 text-blue-700"><Target size={18}/></span>Compatibility Analysis</h3>
      <div className="mb-6 flex items-center gap-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-blue-50 border border-blue-200 text-blue-700">
          <CheckCircle size={28} />
        </div>
        <div>
          <p className="font-bold text-slate-900 text-base">{result.match_level || 'Role Compatibility Evaluated'}</p>
          <p className="text-sm text-slate-500">Your profile and skills have been analyzed against this job's criteria</p>
        </div>
      </div>
      {/* High-level candidate summary: match score, strengths, gaps, and recommendation */}
      <ResultBox title="Strongest Matches" text={result.strongest_matches?.join(', ')||'No strong match evidence identified'} color="green"/>
      <ResultBox title="Skill Gaps" text={result.skill_gaps?.join(', ')||'No confirmed skill gaps'} color="red"/>
      <ResultBox title="Recommendation" text={result.recommendation?.reason||'Manual review recommended'} color="blue"/>
      <button onClick={confirmApplication} disabled={existingApplication||applied} className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-slate-900 py-3 font-bold text-white hover:bg-slate-800 disabled:bg-green-600"><CheckCircle size={18}/>{existingApplication||applied?'Application submitted':'Confirm Application'}</button>
    </div> : !hasProfileSkills && !existingApplication && !applied ? (
      <div className="flex min-h-96 flex-col items-center justify-center rounded-xl border border-amber-200 bg-amber-50/60 p-6 text-center shadow-sm">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 border border-amber-300 text-amber-700">
          <AlertCircle size={32} />
        </div>
        <h3 className="font-bold text-base text-amber-950">Skills or CV Required</h3>
        <p className="mt-2 max-w-sm text-xs text-amber-800 leading-relaxed">
          Match score cannot be calculated because your profile has no skills listed. Please add your technical and soft skills to your profile or upload a CV.
        </p>
        <div className="mt-5 flex flex-wrap justify-center gap-2.5">
          {onNavigateProfile && (
            <button
              onClick={onNavigateProfile}
              className="rounded-xl border border-amber-400 bg-white px-4 py-2.5 text-xs font-bold text-amber-900 hover:bg-amber-100/50 transition shadow-sm"
            >
              ✏️ Add Skills to Profile
            </button>
          )}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 rounded-xl bg-amber-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-amber-700 transition shadow-sm"
          >
            <Upload size={14} /> Upload CV Now
          </button>
        </div>
      </div>
    ) : <div className="flex min-h-96 flex-col items-center justify-center rounded-xl border bg-slate-50 p-6 text-center"><FileText className="mb-4 text-slate-300" size={48}/><h3 className="font-bold text-slate-500">{existingApplication || applied ? 'Application Already Submitted' : 'Ready to Apply'}</h3><p className="mt-2 max-w-sm text-slate-400">{existingApplication || applied ? 'You have already applied for this position. You can track your status in My Applications below.' : 'Your saved profile and experience will be analyzed automatically. Uploading a CV is optional.'}</p></div>}
    </div>
    
    {/* Modal: Duplicate Application Warning */}
    {alreadyAppliedModal && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm" role="dialog" aria-modal="true">
        <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-amber-200">
          <div className="flex items-center gap-3 text-amber-600 mb-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 border border-amber-200">
              <AlertCircle size={26} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Already Applied</h3>
              <p className="text-xs text-amber-700 font-medium">Application record exists</p>
            </div>
          </div>
          <p className="text-sm text-slate-600 leading-relaxed">
            You have already submitted an application for <strong className="text-slate-900">{selectedJob?.title}</strong> at <strong>{selectedJob?.company}</strong>.
          </p>
          <div className="mt-3 text-xs text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1">
            <p><span className="font-semibold text-slate-500">Current Status:</span> <span className="font-bold text-amber-700">{existingApplication?.status || 'Under review'}</span></p>
            <p className="text-[11px] text-slate-400">You can view or withdraw this application under "My Applications".</p>
          </div>
          <div className="mt-6 flex flex-wrap justify-end gap-2">
            <button onClick={showApplications} className="rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-bold text-white hover:bg-blue-700">View My Applications</button>
            <button
              onClick={() => setAlreadyAppliedModal(false)}
              className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-bold text-white hover:bg-slate-800 transition"
            >
              OK, Got it
            </button>
          </div>
        </div>
      </div>
    )}

    {/* Modal: Missing Profile Skills Prompt */}
    {noSkillsModal && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm" role="dialog" aria-modal="true">
        <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-amber-200 space-y-4">
          <div className="flex items-center gap-3 text-amber-600">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 border border-amber-200 shrink-0">
              <AlertCircle size={26} />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Skills or CV Required</h3>
              <p className="text-xs text-amber-700 font-medium">No skills found in your profile</p>
            </div>
          </div>

          <p className="text-sm text-slate-600 leading-relaxed">
            To run an AI compatibility analysis for <strong className="text-slate-900">{selectedJob?.title}</strong>, please add your skills in your profile or upload a CV first.
          </p>

          <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-200 text-xs text-slate-600 space-y-1.5">
            <p className="font-semibold text-slate-800">Choose how to add your skills:</p>
            <p>1. 📁 <strong>Upload CV</strong> — Gemini AI will automatically extract and save all your skills.</p>
            <p>2. ✏️ <strong>Profile Page</strong> — Enter your technical & soft skills manually.</p>
          </div>

          <div className="flex flex-col sm:flex-row justify-end gap-2.5 pt-2">
            <button
              onClick={() => setNoSkillsModal(false)}
              className="rounded-xl border border-slate-300 px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
            {onNavigateProfile && (
              <button
                onClick={() => {
                  setNoSkillsModal(false);
                  onNavigateProfile();
                }}
                className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-xs font-bold text-blue-700 hover:bg-blue-100 transition"
              >
                ✏️ Go to Profile
              </button>
            )}
            <button
              onClick={() => {
                setNoSkillsModal(false);
                fileInputRef.current?.click();
              }}
              className="flex items-center justify-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-blue-700 transition"
            >
              <Upload size={14} /> Upload CV Now
            </button>
          </div>
        </div>
      </div>
    )}

    {/* Section: Candidate's Tracked Applications */}
    <div ref={applicationsRef} className="scroll-mt-24"><ApplicationStatus applications={applications} jobs={jobs} onWithdraw={onWithdraw}/></div>
  </div>;
}

/**
 * Visual highlight box for categorized analysis outputs (Matches, Gaps, Recommendations).
 */
function ResultBox({ title, text, color }) {
  const style = {
    green: 'border-green-100 bg-green-50 text-green-800',
    red: 'border-red-100 bg-red-50 text-red-800',
    blue: 'border-blue-100 bg-blue-50 text-blue-900',
  };
  return (
    <div className={`mb-3 rounded-lg border p-4 ${style[color]}`}>
      <h4 className="mb-2 text-xs font-bold uppercase">{title === 'AI Suggestion' ? 'Career Guidance' : title}</h4>
      <p className="text-sm leading-6">{text}</p>
    </div>
  );
}

/**
 * Clean review panel for a candidate's submitted application.
 * Shows high-level candidate profile, total match score, and AI recommendation.
 * Granular internal evaluation formulas & scoring rubrics are reserved for recruiters.
 */
function ApplicationReview({ application }) {
  const analysis = application.enterpriseEvaluation || application.analysis || {};
  const profile = application.candidateSnapshot || {};
  const score = Number(application.overallScore ?? application.score ?? 0);
  const matchLevel = analysis.match_level || (score >= 80 ? 'Strong Match' : score >= 50 ? 'Moderate Match' : 'Low Match');
  const recommendation = analysis.recommendation || {};
  const recommendationText = recommendation.reason || analysis.ai_suggestion || 'Application received and under recruiter review.';
  const recommendationDecision = recommendation.decision ? recommendation.decision.replaceAll('_', ' ') : null;

  return (
    <div className="border-t border-slate-200 bg-slate-50/70 px-6 py-6">
      <div className="mb-6">
        <h3 className="flex items-center gap-2 text-base font-bold text-slate-900">
          <span className="rounded-lg bg-blue-100 p-1.5 text-blue-700"><Target size={18}/></span>
          Application Compatibility & Status
        </h3>
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        {/* Left Column: Submitted Profile Summary */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Submitted Profile</h4>
          <dl className="mt-4 grid gap-3 text-sm">
            <div>
              <dt className="text-xs text-slate-400">Candidate</dt>
              <dd className="font-semibold text-slate-800">{profile.name || 'Not recorded'}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-400">Headline</dt>
              <dd className="font-semibold text-slate-800">{profile.headline || 'Not provided'}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-400">Experience</dt>
              <dd className="font-semibold text-slate-800">
                {application.candidateExperience ?? profile.experience ?? 0} years / {application.requiredExperience ?? 0} required
              </dd>
            </div>
            <div>
              <dt className="text-xs text-slate-400">CV Document</dt>
              <dd className="font-semibold text-slate-800">{profile.cvFileName || 'Profile application'}</dd>
            </div>
          </dl>
        </div>

        {/* Right Column: Application Status & Review Stage */}
        <div className="flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Application Status</h4>
            <div className="mt-4 flex items-center gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border-2 border-blue-200 bg-blue-50 text-blue-700">
                <Clock3 size={24} />
              </div>
              <div className="space-y-1">
                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">
                  {application.status || 'Under review'}
                </span>
                <p className="text-xs text-slate-500">Application submitted and awaiting company recruiter review</p>
              </div>
            </div>
          </div>

          <div className="mt-4 rounded-lg border border-slate-100 bg-slate-50 p-3 text-xs text-slate-500">
            <p className="font-semibold text-slate-700">Recruiter Evaluation Note</p>
            <p className="mt-0.5 leading-relaxed">
              Internal scoring rubrics and recruiter evaluations are kept confidential to ensure fair hiring.
            </p>
          </div>
        </div>
      </div>

      {/* Full-width Recommendation Box */}
      <div className="mt-5 rounded-xl border border-blue-200 bg-blue-50/70 p-5 shadow-sm">
        <div className="flex items-center justify-between gap-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-blue-800">
            AI Recommendation & Guidance
          </h4>
          {recommendationDecision && (
            <span className="rounded-full bg-blue-600 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide text-white">
              {recommendationDecision}
            </span>
          )}
        </div>
        <p className="mt-2 text-sm leading-6 text-slate-800 font-medium">
          {recommendationText}
        </p>
      </div>
    </div>
  );
}

/**
 * List of applications submitted by the candidate with status tracking and withdrawal dialog.
 */
function ApplicationStatus({ applications, jobs, onWithdraw }) {
  const [pendingWithdrawal, setPendingWithdrawal] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const confirmWithdrawal = () => {
    onWithdraw(pendingWithdrawal.id);
    setPendingWithdrawal(null);
  };

  return (
    <section>
      <div className="mb-4 flex items-end justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-900">My applications</h2>
          <p className="mt-1 text-sm text-slate-500">Track every submitted application in one place.</p>
        </div>
        <span className="text-sm font-semibold text-slate-500">{applications.length} total</span>
      </div>
      <div className="grid gap-3">
        {applications.map((application) => {
          const job = jobs.find((item) => item.id === application.jobId);
          const expanded = expandedId === application.id;
          return (
            <article key={application.id} className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
              <div className="grid gap-4 p-5 sm:grid-cols-[1fr_auto] sm:items-center">
                <div className="flex gap-4">
                  <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                    <Briefcase size={21}/>
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900">{application.jobTitle || job?.title}</h3>
                    <p className="mt-1 text-sm text-slate-500">{application.company || job?.company}</p>
                    <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
                      <span className="flex items-center gap-1"><MapPin size={13}/>{application.location || job?.location}</span>
                      <span className="flex items-center gap-1"><Clock3 size={13}/>Applied {new Date(application.appliedAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2 sm:justify-end">
                  <span className="w-fit rounded-full bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-700">{application.status}</span>
                  <button onClick={() => setExpandedId(expanded ? null : application.id)} className="rounded-lg border border-blue-200 px-3 py-1.5 text-xs font-bold text-blue-700 hover:bg-blue-50">
                    {expanded ? 'Hide Details' : 'Review Details'}
                  </button>
                  <button onClick={() => setPendingWithdrawal(application)} className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-bold text-red-600 hover:bg-red-50">
                    Withdraw Application
                  </button>
                </div>
              </div>
              {expanded && <ApplicationReview application={application}/>}
            </article>
          );
        })}
        {!applications.length && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
            <Briefcase className="mx-auto text-slate-300" size={32}/>
            <p className="mt-3 font-semibold text-slate-600">No applications yet</p>
            <p className="mt-1 text-sm text-slate-400">Analyze a role and confirm your first application.</p>
          </div>
        )}
      </div>

      {/* Confirmation Modal for Application Withdrawal */}
      {pendingWithdrawal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" role="dialog" aria-modal="true" aria-labelledby="withdraw-title">
          <div className="w-full max-w-md rounded-lg bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <h3 id="withdraw-title" className="font-bold text-slate-900">Withdraw Application</h3>
              <button onClick={() => setPendingWithdrawal(null)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100" aria-label="Close">
                <X size={19}/>
              </button>
            </div>
            <div className="p-5">
              <p className="text-sm leading-6 text-slate-600">
                Are you sure you want to withdraw your application for <strong className="text-slate-900">{pendingWithdrawal.jobTitle}</strong>? This application record will be removed.
              </p>
              <div className="mt-6 flex justify-end gap-3">
                <button onClick={() => setPendingWithdrawal(null)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-bold text-slate-700 hover:bg-slate-50">Cancel</button>
                <button onClick={confirmWithdrawal} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-700">Withdraw Application</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

