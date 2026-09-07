import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, Briefcase, CheckCircle, Clock3, FileText, Loader2, MapPin, Search, Target, Upload, X } from 'lucide-react';
import { apiForm, apiRequest } from '../services/api';

export default function CandidateDashboard({ jobs = [], user, token, applications = [], onSaveProfile, onApply, onWithdraw, onNavigateProfile }) {
  const fileInputRef = useRef(null);
  const applicationsRef = useRef(null);
  const [selectedJobId, setSelectedJobId] = useState(jobs[0]?.id || null);
  const [cvText, setCvText] = useState('');
  const [fileName, setFileName] = useState('');
  const [importing, setImporting] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [searchDraft, setSearchDraft] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [applied, setApplied] = useState(false);
  const [alreadyAppliedModal, setAlreadyAppliedModal] = useState(false);
  const [noSkillsModal, setNoSkillsModal] = useState(false);
  const selectedJob = jobs.find((job) => job.id === selectedJobId) || jobs[0];
  const hasProfileSkills = Boolean(
    String(user?.technicalSkills || '').trim() ||
    String(user?.softSkills || '').trim()
  );
  const jobSkills = selectedJob?.skills || 'React, JavaScript, Tailwind, TypeScript, Next.js';
  const filteredJobs = jobs.filter((job) => {
    const query = searchQuery.trim().toLowerCase();
    return !query || [job.title, job.company, job.location, job.type, job.skills].some((value) => String(value || '').toLowerCase().includes(query));
  });
  const existingApplication = applications.find((item) => item.jobId === selectedJob?.id && !['Withdrawn', 'Application Withdrawn'].includes(item.status));
  useEffect(() => {
    if (!existingApplication) setApplied(false);
  }, [existingApplication]);

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

  const handleImport = async (file) => {
    if (!file) return;
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(extension)) { setError('Please choose a PDF, DOCX, or TXT file.'); return; }
    if (file.size > 10 * 1024 * 1024) { setError('CV file must be 10 MB or smaller.'); return; }
    setImporting(true); setError(''); setMessage(''); setResult(null);
    try {
      const uploadData = new FormData(); uploadData.append('file', file);
      const imported = await apiForm(`/api/import-cv?token=${encodeURIComponent(token)}`, uploadData);

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
      onSaveProfile(profileUpdate);
      setCvText(imported.text); setFileName(imported.filename || file.name);
      setResult(analysis);
      
      const techCount = extractedTech.length;
      const softCount = extractedSoft.length;
      const totalCount = extractedSkills.length;
      setMessage(`CV analyzed with Gemini: ${techCount > 0 ? `${techCount} Technical & ${softCount} Soft skills` : `${totalCount} skills`} saved to profile.`);
    } catch (err) { setError(err.message || 'CV processing failed. Please check the backend.'); }
    finally { setImporting(false); if (fileInputRef.current) fileInputRef.current.value = ''; }
  };

  const profileText = [
    `Candidate: ${user.name || ''}`,
    `Professional headline: ${user.headline || ''}`,
    `Technical Skills: ${user.technicalSkills || ''}`,
    `Soft Skills: ${user.softSkills || ''}`,
    `Experience: ${user.experience || 0} years`,
    `About: ${user.bio || ''}`,
    `Location: ${user.location || ''}`,
  ].join('\n');

  const analyze = async () => {
    if (!selectedJob) { setError('Please select a job first.'); return; }
    if (existingApplication || applied) {
      setAlreadyAppliedModal(true);
      setError('You have already applied for this job.');
      return;
    }
    const hasProfileSkills = Boolean(
      String(user.technicalSkills || '').trim() ||
      String(user.softSkills || '').trim()
    );
    if (!hasProfileSkills) {
      setResult(null);
      setNoSkillsModal(true);
      setError('Please add and save skills in your profile before running analysis.');
      return;
    }
    setLoading(true); setError('');
    try {
      const analysis = await apiRequest(`/api/jobs/${selectedJob.id}/candidate-evaluation?token=${encodeURIComponent(token)}`, { method: 'POST' });
      setResult(analysis);
    } catch (err) { setError(err.message || 'Could not connect to the analysis service.'); }
    finally { setLoading(false); }
  };

  const showApplications = () => {
    setAlreadyAppliedModal(false);
    setTimeout(() => applicationsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 0);
  };

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

    <section>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><h2 className="text-xl font-bold">Find your next role</h2><p className="mt-1 text-sm text-slate-500">Search by title, company, skill, or location.</p></div><form onSubmit={(event)=>{event.preventDefault();setSearchQuery(searchDraft);}} className="flex w-full max-w-xl gap-2"><div className="relative flex-1"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18}/><input value={searchDraft} onChange={(e)=>setSearchDraft(e.target.value)} placeholder="Search jobs" className="h-11 w-full rounded-lg border border-slate-300 pl-10 pr-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"/></div><button className="h-11 rounded-lg bg-slate-900 px-5 text-sm font-bold text-white hover:bg-slate-800">Search</button></form></div>
      <div className="flex gap-3 overflow-x-auto pb-2">{filteredJobs.map((job) => <button key={job.id} onClick={() => { setSelectedJobId(job.id); setResult(null); setApplied(false); }} className={`min-w-64 rounded-lg border p-4 text-left transition ${selectedJob?.id === job.id ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-100' : 'border-slate-200 bg-white hover:border-slate-300'}`}><p className="font-bold">{job.title}</p><p className="mt-1 text-sm text-slate-500">{job.company} · {job.location}</p><div className="mt-3 flex gap-2"><span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold">{job.type}</span><span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700">{Number(job.experience || 0)}+ yrs</span></div></button>)}{!filteredJobs.length&&<div className="w-full rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">No jobs match “{searchQuery}”.</div>}</div>
    </section>

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

    {hasProfileSkills && result && !existingApplication && !applied ? <div className="relative overflow-hidden rounded-xl border bg-white p-6 shadow-sm">
      <div className="absolute inset-x-0 top-0 h-1 bg-blue-600"/>
      <h3 className="mb-6 flex items-center gap-2 text-lg font-bold"><span className="rounded-lg bg-blue-100 p-1.5 text-blue-700"><Target size={18}/></span>Compatibility Analysis</h3>
      <div className="mb-6 flex items-center gap-4"><div className={`flex h-16 w-16 items-center justify-center rounded-full border-4 ${result.score>=80?'border-green-500 text-green-600':result.score>=50?'border-orange-500 text-orange-600':'border-red-500 text-red-600'}`}><b>{result.score}%</b></div><div><p className="font-bold">{result.match_level||(result.score>=80?'Strong Match':result.score>=50?'Moderate Match':'Low Match')}</p><p className="text-sm text-slate-500">Complete database profile matched against this job</p><p className="mt-1 text-xs font-semibold text-emerald-700">Evidence confidence: {result.evidence_confidence??0}%</p></div></div>
      {result.score_breakdown?.technical_skills ? <div className="mb-5 grid items-start gap-2 sm:grid-cols-2">{Object.entries(result.score_breakdown).map(([key,item])=><CategoryScoreCard key={key} category={key} item={item} evidenceConfidence={result.evidence_confidence}/>)}</div> : result.score_breakdown && <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-bold uppercase text-slate-500">Legacy score</p></div>}
      {result.skill_analysis?.length>0&&<div className="mb-4 rounded-lg border border-slate-200 bg-white p-4"><p className="mb-2 text-xs font-bold uppercase text-slate-500">Important skill analysis</p>{result.skill_analysis.map((item)=><div key={item.skill} className="border-t border-slate-100 py-2 first:border-0"><div className="flex justify-between gap-3 text-xs"><span className="font-bold text-slate-800">{item.skill} · {item.candidate_match?.replaceAll('_',' ')}</span><span className="font-semibold text-blue-700">{item.score_percentage}%</span></div><p className="mt-1 text-xs text-slate-500">{item.explanation}</p></div>)}</div>}
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

    <div ref={applicationsRef} className="scroll-mt-24"><ApplicationStatus applications={applications} jobs={jobs} onWithdraw={onWithdraw}/></div>
  </div>;
}


function ResultBox({ title, text, color }) { const style={green:'border-green-100 bg-green-50 text-green-800',red:'border-red-100 bg-red-50 text-red-800',blue:'border-blue-100 bg-blue-50 text-blue-900'}; return <div className={`mb-3 rounded-lg border p-4 ${style[color]}`}><h4 className="mb-2 text-xs font-bold uppercase">{title === 'AI Suggestion' ? 'Career Guidance' : title}</h4><p className="text-sm leading-6">{text}</p></div>; }

function SkillScoreDetails({ skills }) {
  const statusStyle = { Full: 'bg-green-50 text-green-700', Partial: 'bg-amber-50 text-amber-700', Missing: 'bg-red-50 text-red-700' };
  return <div className="mb-4 overflow-hidden rounded-lg border border-slate-200"><div className="border-b border-slate-200 bg-white px-4 py-3"><h4 className="text-xs font-bold uppercase text-slate-600">Skill Score Details</h4></div><div className="divide-y divide-slate-100">{skills.map((item)=><div key={item.skill} className="grid gap-2 px-4 py-3 sm:grid-cols-[minmax(110px,0.7fr)_90px_1fr_auto] sm:items-center"><span className="text-sm font-bold text-slate-900">{item.skill}</span><span className={`w-fit rounded-full px-2 py-1 text-[11px] font-bold ${statusStyle[item.status]}`}>{item.status}</span><span className="text-xs leading-5 text-slate-500">{item.evidence}</span><span className="text-sm font-bold tabular-nums text-slate-700">{item.points}/{item.max_points}</span></div>)}</div></div>;
}

function CategoryScoreCard({ category, item = {}, evidenceConfidence }) {
  const [expanded, setExpanded] = useState(false);
  const score = Number(item.score ?? item.weighted_score ?? 0);
  const maximum = Number(item.max ?? item.maximum_score ?? 0);
  const percentage = maximum > 0 ? Math.round((score / maximum) * 1000) / 10 : 0;
  const evidence = Array.isArray(item.evidence) ? item.evidence.filter(Boolean) : [];
  return <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
    <div className="flex items-center justify-between gap-3"><span className="text-xs font-bold capitalize text-slate-700">{category.replaceAll('_',' ')}</span><span className="text-sm font-bold text-blue-700">{score}/{maximum}</span></div>
    <p className="mt-1 text-xs leading-5 text-slate-500">{item.reason || 'No scoring explanation was recorded.'}</p>
    <button type="button" onClick={() => setExpanded((value) => !value)} className="mt-2 text-xs font-bold text-blue-600 hover:text-blue-800 hover:underline">{expanded ? 'Hide calculation' : 'How was this calculated?'}</button>
    {expanded && <div className="mt-3 space-y-2 rounded-lg border border-blue-100 bg-blue-50/60 p-3 text-xs leading-5 text-slate-700">
      <p><strong>Formula:</strong> {score} awarded ÷ {maximum} maximum × 100 = <strong>{percentage}%</strong> category achievement.</p>
      <p><strong>Weight:</strong> This category contributes a maximum of {maximum} marks to the 100-mark job-match score.</p>
      <p><strong>Assessment:</strong> {item.reason || 'No relevant evidence was identified.'}</p>
      {evidenceConfidence != null && <p><strong>Overall evidence confidence:</strong> {evidenceConfidence}%. This is shown separately and is not added to the marks.</p>}
      {evidence.length > 0 ? <div><strong>Evidence used:</strong><ul className="mt-1 list-disc pl-5">{evidence.map((value, index) => <li key={index}>{typeof value === 'string' ? value : JSON.stringify(value)}</li>)}</ul></div> : <p className="text-slate-500"><strong>Evidence detail:</strong> The recorded reason summarizes the database evidence used. Missing external verification is not automatically treated as failure.</p>}
    </div>}
  </div>;
}

function ApplicationReview({ application }) {
  const analysis = application.enterpriseEvaluation || application.analysis || {};
  const profile = application.candidateSnapshot || {};
  const breakdown = analysis.score_breakdown;
  const skills = analysis.skill_breakdown || [];
  const categories = breakdown && breakdown.technical_skills ? Object.entries(breakdown) : [];
  return <div className="border-t border-slate-200 bg-slate-50 px-5 py-5"><h3 className="mb-5 flex items-center gap-2 text-lg font-bold text-slate-900"><span className="rounded-lg bg-blue-100 p-1.5 text-blue-700"><Target size={18}/></span>Compatibility Analysis</h3><div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]"><div><h4 className="text-xs font-bold uppercase text-slate-500">Submitted Profile</h4><dl className="mt-3 grid gap-3 text-sm"><div><dt className="text-xs text-slate-400">Candidate</dt><dd className="font-semibold text-slate-800">{profile.name||'Not recorded'}</dd></div><div><dt className="text-xs text-slate-400">Headline</dt><dd className="font-semibold text-slate-800">{profile.headline||'Not provided'}</dd></div><div><dt className="text-xs text-slate-400">Experience</dt><dd className="font-semibold text-slate-800">{application.candidateExperience??profile.experience??0} years / {application.requiredExperience??0} required</dd></div><div><dt className="text-xs text-slate-400">CV</dt><dd className="font-semibold text-slate-800">{profile.cvFileName||'Profile application'}</dd></div></dl></div><div><h4 className="text-xs font-bold uppercase text-slate-500">Application Score</h4><div className="mt-3 flex flex-wrap items-center gap-2 text-sm font-bold"><span className="rounded-lg bg-blue-600 px-3 py-2 text-white">{application.overallScore??application.score}% total</span>{analysis.evidence_confidence!=null&&<span className="rounded-lg bg-emerald-50 px-3 py-2 text-emerald-700">Evidence confidence {analysis.evidence_confidence}%</span>}</div>{categories.length>0?<div className="mt-4 grid items-start gap-2 sm:grid-cols-2">{categories.map(([key,item])=><CategoryScoreCard key={key} category={key} item={item} evidenceConfidence={analysis.evidence_confidence}/>)}</div>:skills.length>0?<div className="mt-4"><SkillScoreDetails skills={skills}/></div>:<p className="mt-4 text-sm text-slate-500">Detailed category scoring was not saved for this earlier application.</p>}</div></div><div className="mt-5 border-t border-slate-200 pt-5"><h4 className="text-xs font-bold uppercase text-blue-700">Recommendation</h4><p className="mt-2 text-sm leading-6 text-slate-700">{analysis.recommendation?.reason||analysis.ai_suggestion||'Manual recruiter review is recommended where evidence is incomplete.'}</p></div></div>;
}

function ApplicationStatus({ applications, jobs, onWithdraw }) {
  const [pendingWithdrawal, setPendingWithdrawal] = useState(null);
  const [expandedId, setExpandedId] = useState(null);
  const confirmWithdrawal = () => {
    onWithdraw(pendingWithdrawal.id);
    setPendingWithdrawal(null);
  };

  return <section>
    <div className="mb-4 flex items-end justify-between"><div><h2 className="text-xl font-bold text-slate-900">My applications</h2><p className="mt-1 text-sm text-slate-500">Track every submitted application in one place.</p></div><span className="text-sm font-semibold text-slate-500">{applications.length} total</span></div>
    <div className="grid gap-3">{applications.map((application)=>{const job=jobs.find((item)=>item.id===application.jobId);const expanded=expandedId===application.id;return <article key={application.id} className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm"><div className="grid gap-4 p-5 sm:grid-cols-[1fr_auto] sm:items-center"><div className="flex gap-4"><div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700"><Briefcase size={21}/></div><div><h3 className="font-bold text-slate-900">{application.jobTitle||job?.title}</h3><p className="mt-1 text-sm text-slate-500">{application.company||job?.company}</p><div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500"><span className="flex items-center gap-1"><MapPin size={13}/>{application.location||job?.location}</span><span className="flex items-center gap-1"><Clock3 size={13}/>Applied {new Date(application.appliedAt).toLocaleDateString()}</span><span className="font-bold text-blue-700">{application.score}% match</span></div></div></div><div className="flex flex-wrap items-center gap-2 sm:justify-end"><span className="w-fit rounded-full bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-700">{application.status}</span><button onClick={()=>setExpandedId(expanded?null:application.id)} className="rounded-lg border border-blue-200 px-3 py-1.5 text-xs font-bold text-blue-700 hover:bg-blue-50">{expanded?'Hide Details':'Review Details'}</button><button onClick={()=>setPendingWithdrawal(application)} className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-bold text-red-600 hover:bg-red-50">Withdraw Application</button></div></div>{expanded&&<ApplicationReview application={application}/>}</article>})}{!applications.length&&<div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center"><Briefcase className="mx-auto text-slate-300" size={32}/><p className="mt-3 font-semibold text-slate-600">No applications yet</p><p className="mt-1 text-sm text-slate-400">Analyze a role and confirm your first application.</p></div>}</div>
    {pendingWithdrawal && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" role="dialog" aria-modal="true" aria-labelledby="withdraw-title"><div className="w-full max-w-md rounded-lg bg-white shadow-2xl"><div className="flex items-center justify-between border-b border-slate-200 px-5 py-4"><h3 id="withdraw-title" className="font-bold text-slate-900">Withdraw Application</h3><button onClick={()=>setPendingWithdrawal(null)} className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100" aria-label="Close"><X size={19}/></button></div><div className="p-5"><p className="text-sm leading-6 text-slate-600">Are you sure you want to withdraw your application for <strong className="text-slate-900">{pendingWithdrawal.jobTitle}</strong>? This application record will be removed.</p><div className="mt-6 flex justify-end gap-3"><button onClick={()=>setPendingWithdrawal(null)} className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-bold text-slate-700 hover:bg-slate-50">Cancel</button><button onClick={confirmWithdrawal} className="rounded-lg bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-700">Withdraw Application</button></div></div></div></div>}
  </section>;
}
