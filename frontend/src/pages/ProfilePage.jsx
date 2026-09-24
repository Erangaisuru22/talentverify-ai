/**
 * @file ProfilePage.jsx
 * @description Candidate and Recruiter profile management center.
 * Enables candidates to edit core contact info, upload profile photos,
 * parse CVs with Gemini AI, verify third-party credentials (GitHub, LinkedIn, Portfolio),
 * explore verified skill matrices, track historical evidence snapshots, and maintain structured records.
 */

import React, { useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  Building2,
  CheckCircle,
  CheckCircle2,
  ChevronRight,
  Code,
  Cpu,
  Eye,
  ExternalLink,
  FileCode2,
  FileText,
  FolderGit2,
  GitBranch,
  Github,
  GitPullRequest,
  GraduationCap,
  HeartHandshake,
  History,
  Languages,
  Layers,
  Loader2,
  Mail,
  MapPin,
  Save,
  Settings,
  ShieldCheck,
  Sparkles,
  Upload,
  User,
  X,
  XCircle,
} from 'lucide-react';
import { apiForm, apiRequest } from '../services/api';

/**
 * User Profile Settings and Evidence Verification Component.
 *
 * @param {Object} props
 * @param {Object} props.user - Active user profile object.
 * @param {string} props.token - Active authentication session token.
 * @param {(profile: Object) => Promise<any>} props.onSave - Save callback to update user profile in parent state.
 */
export default function ProfilePage({ user, token, onSave }) {
  // --- Form Input States ---
  const [form, setForm] = useState({
    name: user.name || '',
    phone: user.phone || '',
    location: user.location || '',
    headline: user.headline || '',
    company: user.company || '',
    bio: user.bio || '',
    technicalSkills: user.technicalSkills || '',
    softSkills: user.softSkills || '',
    skills: user.skills || '',
    experience: user.experience || '',
    linkedinUrl: user.linkedinUrl || '',
    githubUrl: user.githubUrl || '',
    portfolioUrl: user.portfolioUrl || '',
  });

  // --- Feedback & Notification States ---
  const [saved, setSaved] = useState(false);              // Save success confirmation indicator
  const [cvImporting, setCvImporting] = useState(false);  // CV parsing in progress
  const [cvMessage, setCvMessage] = useState('');        // CV import success message
  const [cvError, setCvError] = useState('');            // CV import error message

  // --- External Verification & Evidence States ---
  const [githubEvidence, setGithubEvidence] = useState(null); // GitHub verification analysis & repos
  const [structured, setStructured] = useState({ languages: [], projects: [], education: [], cv_analyses: [] }); // DB structured records
  const [skillMatrix, setSkillMatrix] = useState([]);         // Multi-source verified skill matrix
  const [showSkillMatrixDetails, setShowSkillMatrixDetails] = useState(false);
  const [showAllSkillMatrix, setShowAllSkillMatrix] = useState(false);
  const [githubLoading, setGithubLoading] = useState(false);
  const [githubError, setGithubError] = useState('');
  const [linkedinLoading, setLinkedinLoading] = useState(false);
  const [linkedinError, setLinkedinError] = useState('');
  const [portfolioLoading, setPortfolioLoading] = useState(false);
  const [portfolioError, setPortfolioError] = useState('');
  const [portfolioEvidence, setPortfolioEvidence] = useState(null);
  const [linkedinVerification, setLinkedinVerification] = useState(user.linkedinVerification || null);
  const [linkedinHistory, setLinkedinHistory] = useState([]);
  const [showLinkedinHistory, setShowLinkedinHistory] = useState(false);
  const [selectedSkillDrillDown, setSelectedSkillDrillDown] = useState(null);

  // --- Snapshot History & Comparison States ---
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [snapshots, setSnapshots] = useState([]);
  const [compareData, setCompareData] = useState(null);
  const [compareFromId, setCompareFromId] = useState('');
  const [compareToId, setCompareToId] = useState('');

  // --- Profile Photo & Visibility Settings ---
  const [profilePhotoUrl, setProfilePhotoUrl] = useState(user.profilePhotoUrl || '');
  const [photoUploading, setPhotoUploading] = useState(false);
  const [photoError, setPhotoError] = useState('');
  const [showPhotoSettings, setShowPhotoSettings] = useState(false);
  const [photoVisibleToRecruiters, setPhotoVisibleToRecruiters] = useState(user.photoVisibleToRecruiters === true);
  const [showQualityExplanation, setShowQualityExplanation] = useState(false);

  // --- DOM References ---
  const fileInputRef = useRef(null);
  const photoInputRef = useRef(null);

  /** Helper to update a specific field in the profile form state */
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  /**
   * Uploads candidate's profile picture to backend storage.
   * @param {File} file - Image file (JPG, PNG, WebP up to 2MB).
   */
  const uploadPhoto = async (file) => {
    if (!file) return;
    setPhotoError('');
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 2 * 1024 * 1024) {
      setPhotoError('Choose a JPG, PNG, or WebP image up to 2 MB.');
      return;
    }
    setPhotoUploading(true);
    try {
      const data = new FormData(); data.append('file', file);
      const result = await apiForm(`/api/profile/photo?token=${encodeURIComponent(token)}`, data);
      setProfilePhotoUrl(result.profilePhotoUrl);
    } catch (error) { setPhotoError(error.message); }
    finally { setPhotoUploading(false); }
  };

  /**
   * Loads structured candidate records, skill matrix, and verification snapshots from the backend.
   */
  const loadData = () => {
    if (user.role !== 'candidate') return;
    apiRequest(`/api/candidates/me/structured?token=${encodeURIComponent(token)}`)
      .then((data) => {
        setStructured(data);
        if (data.github) {
          setGithubEvidence(data.github);
          if (data.github.github_url) update('githubUrl', data.github.github_url);
        }
        if (data.linkedin) setLinkedinVerification(data.linkedin);
        setLinkedinHistory(data.linkedin_history || []);
        if (data.portfolio) {
          setPortfolioEvidence(data.portfolio);
          update('portfolioUrl', data.portfolio.portfolio_url);
        }
      })
      .catch(() => {});

    apiRequest(`/api/candidates/me/skills/matrix?token=${encodeURIComponent(token)}`)
      .then((data) => setSkillMatrix(data || []))
      .catch(() => {});
  };

  // Synchronize candidate data on mount or token change
  useEffect(() => {

    loadData();
  }, [token, user.role]);

  /**
   * Triggers background GitHub repository analysis and commit activity verification.
   */
  const verifyGithub = async () => {
    setGithubLoading(true);
    setGithubError('');
    try {
      const evidence = await apiRequest(`/api/candidates/me/github/verify?token=${encodeURIComponent(token)}`, {
        method: 'POST',
        body: JSON.stringify({ data: { github_url: form.githubUrl } }),
      });
      setGithubEvidence(evidence);
      update('githubUrl', evidence.github_url);
      await onSave({ githubUrl: evidence.github_url });
      loadData();
    } catch (error) {
      setGithubError(error.message);
    } finally {
      setGithubLoading(false);
    }
  };

  /**
   * Verifies the candidate's LinkedIn profile URL format and structure.
   */
  const verifyLinkedinUrl = async () => {
    setLinkedinLoading(true);
    setLinkedinError('');
    try {
      const verification = await apiRequest(`/api/candidates/me/linkedin/verify?token=${encodeURIComponent(token)}`, {
        method: 'POST',
        body: JSON.stringify({ data: { linkedin_url: form.linkedinUrl } }),
      });
      setLinkedinVerification(verification);
      update('linkedinUrl', verification.url);
      await onSave({ linkedinUrl: verification.url });
      loadData();
    } catch (error) {
      setLinkedinError(error.message);
    } finally {
      setLinkedinLoading(false);
    }
  };

  /**
   * Initiates official OAuth connection to LinkedIn to import verified employment history.
   */
  const connectLinkedin = async () => {
    setLinkedinLoading(true);
    setLinkedinError('');
    try {
      const result = await apiRequest(`/api/candidates/me/linkedin/connect?token=${encodeURIComponent(token)}`, { method: 'POST' });
      window.location.assign(result.authorization_url);
    } catch (error) {
      setLinkedinError(error.message);
      // Keep the last API-verified snapshot visible when LinkedIn is unavailable.
      setLinkedinLoading(false);
    }
  };

  /**
   * Scrapes and verifies candidate's personal portfolio or project site.
   */
  const verifyPortfolio = async () => {
    setPortfolioLoading(true); setPortfolioError('');
    try {
      const evidence = await apiRequest(`/api/candidates/me/portfolio/verify?token=${encodeURIComponent(token)}`, {
        method: 'POST', body: JSON.stringify({ data: { portfolio_url: form.portfolioUrl } }),
      });
      setPortfolioEvidence(evidence);
      update('portfolioUrl', evidence.portfolio_url);
      await onSave({ portfolioUrl: evidence.portfolio_url });
      loadData();
    } catch (error) { setPortfolioError(error.message); }
    finally { setPortfolioLoading(false); }
  };

  /**
   * Fetches historical GitHub evidence snapshots for diffing and progress tracking.
   */
  const openHistory = async () => {
    setShowHistoryModal(true);
    try {
      const history = await apiRequest(`/api/candidates/me/github/snapshots?token=${encodeURIComponent(token)}`);
      setSnapshots(history || []);
      if (history && history.length >= 2) {
        setCompareFromId(history[1].id);
        setCompareToId(history[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  /**
   * Computes differences and delta metrics between two historical evidence snapshots.
   */
  const runComparison = async () => {
    if (!compareFromId || !compareToId) return;
    try {
      const res = await apiRequest(`/api/candidates/me/github/compare?from_id=${encodeURIComponent(compareFromId)}&to_id=${encodeURIComponent(compareToId)}&token=${encodeURIComponent(token)}`);
      setCompareData(res);
    } catch (e) {
      console.error(e);
    }
  };

  // Check if candidate currently has skills populated
  const hasSkills = Boolean(String(form.technicalSkills).trim() || String(form.softSkills).trim());

  // Technical skill filtering and cross-verification matching against skill matrix
  const profileTechnicalSkills = String(form.technicalSkills || '')
    .split(',')
    .map((skill) => skill.trim())
    .filter(Boolean);
  const isProfileTechnicalSkill = (value) => {
    const key = String(value || '').trim().toLowerCase();
    return profileTechnicalSkills.some((skill) => {
      const profileKey = skill.toLowerCase();
      return profileKey === key || (
        Math.min(profileKey.length, key.length) >= 3
        && (profileKey.includes(key) || key.includes(profileKey))
      );
    });
  };
  const savedTechnicalSkillKeys = new Set(
    String(user.technicalSkills || '').split(',').map((skill) => skill.trim().toLowerCase()).filter(Boolean),
  );
  const profileSkillMatrix = skillMatrix.filter(
    (item) => savedTechnicalSkillKeys.has(String(item.skill || '').trim().toLowerCase()),
  );
  const displayedProfileSkillMatrix = showAllSkillMatrix ? profileSkillMatrix : profileSkillMatrix.slice(0, 32);
  const profileQualityScore = githubEvidence?.analysis?.code_quality_score
    ?? (githubEvidence?.repositories?.length
      ? Math.round(
        githubEvidence.repositories.reduce((total, repo) => total + Number(repo.code_quality?.score || 0), 0)
        / githubEvidence.repositories.length,
      )
      : 0);

  /**
   * Merges existing skill strings with newly extracted skill items.
   */
  const mergeSkills = (existing, extracted) => {
    const merged = [];
    const seen = new Set();
    [...String(existing || '').split(','), ...extracted].forEach((skill) => {
      const clean = String(skill).trim();
      const key = clean.toLowerCase();
      if (clean && !seen.has(key)) {
        seen.add(key);
        merged.push(clean);
      }
    });
    return merged.join(', ');
  };

  /**
   * Uploads and parses CV using Gemini AI to extract contact details,
   * work experience timeline, and categorized skills.
   * @param {File} file - Selected CV file.
   */
  const handleCvImport = async (file) => {
    if (!file) return;
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(extension)) {
      setCvError('Please choose a PDF, DOCX, or TXT file.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setCvError('CV file must be 10 MB or smaller.');
      return;
    }
    setCvImporting(true);
    setCvError('');
    setCvMessage('');
    try {
      const uploadData = new FormData();
      uploadData.append('file', file);
      const imported = await apiForm(`/api/import-cv?token=${encodeURIComponent(token)}`, uploadData);

      let details, extractedTech, extractedSoft, extractedSkills;
      if (imported.structured_extraction) {
        const extracted = imported.structured_extraction;
        extractedTech = (extracted.technical_skills || []).map((item) => item.skill);
        extractedSoft = (extracted.soft_skills || []).map((item) => item.skill);
        extractedSkills = [...extractedTech, ...extractedSoft];
        const months = (extracted.experience || []).reduce((sum, item) => sum + Number(item.duration_months || 0), 0);
        details = {
          headline: extracted.personal_info?.professional_title || '',
          phone: extracted.personal_info?.phone || '',
          location: extracted.personal_info?.location || '',
          bio: '',
          experience: months / 12,
          technical_skills: extractedTech,
          soft_skills: extractedSoft,
        };
      } else {
        const analysisData = new FormData();
        analysisData.append('job_title', 'General Candidate Profile');
        analysisData.append('job_skills', 'General');
        analysisData.append('cv_text', imported.text);
        analysisData.append('candidate_experience', Number(form.experience || 0));
        analysisData.append('required_experience', 0);
        const analysis = await apiForm('/api/analyze-cv', analysisData);
        details = analysis.profile_details || {};
        extractedTech = details.technical_skills || [];
        extractedSoft = details.soft_skills || [];
        extractedSkills = analysis.extracted_skills || [...extractedTech, ...extractedSoft];
      }

      const newTechSkills = mergeSkills(form.technicalSkills || '', extractedTech);
      const newSoftSkills = mergeSkills(form.softSkills || '', extractedSoft);
      const combinedSkills = mergeSkills(form.skills, [...extractedSkills, ...extractedTech, ...extractedSoft]);

      const newHeadline = details.headline || form.headline || '';
      const newPhone = details.phone || form.phone || '';
      const newLocation = details.location || form.location || '';
      const newBio = details.bio || form.bio || '';
      const newExperience = Math.max(Number(details.experience || 0), Number(form.experience || 0));

      const profileUpdate = {
        name: form.name,
        company: form.company,
        technicalSkills: newTechSkills,
        softSkills: newSoftSkills,
        skills: combinedSkills,
        headline: newHeadline,
        phone: newPhone,
        location: newLocation,
        bio: newBio,
        experience: newExperience,
        cvFileName: imported.filename || file.name,
        cvImportedAt: new Date().toISOString(),
      };

      setForm((current) => ({ ...current, ...profileUpdate }));
      onSave(profileUpdate);
      loadData();

      const techCount = extractedTech.length;
      const softCount = extractedSoft.length;
      const totalCount = extractedSkills.length;
      setCvMessage(
        `CV parsed with Gemini AI: ${techCount > 0 ? `${techCount} Technical & ${softCount} Soft skills` : `${totalCount} skills`} extracted and profile saved!`
      );
    } catch (err) {
      setCvError(err.message || 'CV processing failed. Please check the backend.');
    } finally {
      setCvImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };


  /**
   * Submits the candidate's updated profile form to backend storage.
   */
  const submit = (event) => {
    event.preventDefault();
    const techList = form.technicalSkills.split(',').map((s) => s.trim()).filter(Boolean);
    const softList = form.softSkills.split(',').map((s) => s.trim()).filter(Boolean);
    const combined = Array.from(new Set([...techList, ...softList])).join(', ');

    const payload = {
      ...form,
      skills: combined,
    };
    onSave(payload);
    setSaved(true);
    setTimeout(() => setSaved(false), 2200);
    loadData();
  };

  const techBadges = (form.technicalSkills || '').split(',').map((s) => s.trim()).filter(Boolean);
  const softBadges = (form.softSkills || '').split(',').map((s) => s.trim()).filter(Boolean);

  /**
   * Deletes a technical skill from the database and updates profile state.
   * @param {string} skillToRemove - Skill name to remove.
   */
  const removeTechSkill = async (skillToRemove) => {
    const updatedList = techBadges.filter((s) => s.toLowerCase() !== skillToRemove.toLowerCase());
    try {
      await apiRequest(`/api/candidates/me/skills?skill=${encodeURIComponent(skillToRemove)}&kind=technical&token=${encodeURIComponent(token)}`, { method: 'DELETE' });
      update('technicalSkills', updatedList.join(', '));
      await onSave({ technicalSkills: updatedList.join(', '), softSkills: form.softSkills });
      loadData();
    } catch (error) { setCvError(error.message); }
  };

  /**
   * Deletes a soft skill from the database and updates profile state.
   * @param {string} skillToRemove - Skill name to remove.
   */
  const removeSoftSkill = async (skillToRemove) => {
    const updatedList = softBadges.filter((s) => s.toLowerCase() !== skillToRemove.toLowerCase());
    try {
      await apiRequest(`/api/candidates/me/skills?skill=${encodeURIComponent(skillToRemove)}&kind=soft&token=${encodeURIComponent(token)}`, { method: 'DELETE' });
      update('softSkills', updatedList.join(', '));
      await onSave({ technicalSkills: form.technicalSkills, softSkills: updatedList.join(', ') });
      loadData();
    } catch (error) { setCvError(error.message); }
  };


  return (
    <div className="mx-auto min-w-0 max-w-4xl space-y-6">
      <div className="rounded-2xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 p-5 text-white shadow-md sm:p-7">
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="flex h-20 w-20 overflow-hidden items-center justify-center rounded-full bg-white/20 backdrop-blur-md ring-2 ring-white/40">
              {profilePhotoUrl ? <img src={profilePhotoUrl} alt="Profile" className="h-full w-full object-cover" /> : <User size={32} />}
            </div>
            <input ref={photoInputRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(e) => uploadPhoto(e.target.files?.[0])} />
            <button type="button" disabled={photoUploading} onClick={() => setShowPhotoSettings(true)} className="absolute -bottom-2 -right-2 rounded-full bg-white p-2 text-blue-700 shadow-md disabled:opacity-60" title="Profile photo settings">
              {photoUploading ? <Loader2 size={15} className="animate-spin" /> : <Settings size={15} />}
            </button>
          </div>
          <div>
            <p className="text-sm font-medium text-blue-100 capitalize">{user.role} profile</p>
            <h2 className="text-2xl font-extrabold tracking-tight">{user.name}</h2>
            <p className="mt-1 flex min-w-0 items-center gap-1.5 break-all text-sm text-blue-100">
              <Mail className="shrink-0" size={14} />
              {user.email}
            </p>
          </div>
        </div>
        {photoError && <p className="mt-4 rounded-lg bg-red-500/20 px-3 py-2 text-sm text-white">{photoError}</p>}
      </div>

      {showPhotoSettings && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" role="dialog" aria-modal="true">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b pb-4">
              <div><h3 className="font-bold text-slate-900">Profile photo settings</h3><p className="text-xs text-slate-500">Manage your professional photo and recruiter privacy.</p></div>
              <button type="button" onClick={() => setShowPhotoSettings(false)} className="rounded-lg p-2 hover:bg-slate-100"><X size={19} /></button>
            </div>
            <div className="mt-5 flex flex-col items-center">
              <div className="flex h-28 w-28 overflow-hidden items-center justify-center rounded-full bg-slate-100 text-slate-500 ring-4 ring-slate-200">
                {profilePhotoUrl ? <img src={profilePhotoUrl} alt="Profile preview" className="h-full w-full object-cover" /> : <User size={42} />}
              </div>
              <button type="button" disabled={photoUploading} onClick={() => photoInputRef.current?.click()} className="mt-4 flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-60">
                <Upload size={16} /> {profilePhotoUrl ? 'Change photo' : 'Upload photo'}
              </button>
              <p className="mt-2 text-xs text-slate-500">JPG, PNG, or WebP · maximum 2 MB</p>
            </div>
            <label className="mt-6 flex items-start justify-between gap-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <span><span className="block text-sm font-bold text-slate-900">Recruiters can see my photo</span><span className="mt-1 block text-xs leading-5 text-slate-500">When disabled, recruiters only see a generic avatar. This does not affect your evaluation score.</span></span>
              <input type="checkbox" checked={photoVisibleToRecruiters} onChange={async (event) => { const visible = event.target.checked; setPhotoVisibleToRecruiters(visible); await onSave({ photoVisibleToRecruiters: visible }); }} className="mt-1 h-5 w-5 accent-blue-600" />
            </label>
          </div>
        </div>
      )}

      {user.role === 'candidate' && !hasSkills && (
        <div className="rounded-2xl border border-amber-300 bg-amber-50/90 p-5 text-amber-900 shadow-sm flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 border border-amber-300 text-amber-700">
            <AlertCircle size={22} />
          </div>
          <div className="space-y-1">
            <h4 className="font-bold text-base text-amber-950">Action Required: No Skills Found in Profile</h4>
            <p className="text-sm text-amber-800 leading-relaxed">
              Your profile does not have any technical or soft skills listed. To apply for jobs and run AI compatibility analysis, <strong>import your CV below</strong> or <strong>type your skills manually</strong> into the skills section.
            </p>
          </div>
        </div>
      )}

      {user.role === 'candidate' && (
        <div className="space-y-4 rounded-2xl border border-blue-200 bg-white p-4 shadow-sm sm:p-7">
          <div className="flex items-center justify-between border-b pb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <FileText className="text-blue-600" size={20} /> Import CV to Auto-Fill Skills
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Upload your CV to automatically extract technical skills, soft skills, and experience with Gemini AI.</p>
            </div>
          </div>

          <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={(e) => handleCvImport(e.target.files?.[0])} />
          <button
            type="button"
            disabled={cvImporting}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => { e.preventDefault(); handleCvImport(e.dataTransfer.files?.[0]); }}
            className="w-full rounded-xl border-2 border-dashed border-blue-300 bg-blue-50/60 p-6 text-center transition hover:bg-blue-100/50 disabled:opacity-60"
          >
            {cvImporting ? <Loader2 className="mx-auto mb-2 animate-spin text-blue-600" size={24} /> : <Upload className="mx-auto mb-2 text-blue-600" size={24} />}
            <p className="text-sm font-bold text-slate-800">{cvImporting ? 'Gemini AI is parsing your CV & extracting skills...' : 'Drop CV here or click to browse file'}</p>
            <p className="mt-1 text-xs text-slate-500">PDF, DOCX or TXT · Max 10 MB</p>
          </button>

          {cvMessage && (
            <p className="mt-2 flex items-center gap-2 rounded-lg bg-green-50 p-3 text-sm font-semibold text-green-700 border border-green-200">
              <CheckCircle size={18} /> {cvMessage}
            </p>
          )}
          {cvError && (
            <p role="alert" className="mt-2 rounded-lg bg-red-50 p-3 text-sm font-medium text-red-700 border border-red-200">
              {cvError}
            </p>
          )}
        </div>
      )}

      {/* Multi-Source Technical Skills Matrix */}
      {user.role === 'candidate' && profileSkillMatrix.length > 0 && (
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-7">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b pb-4">
            <div>
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Layers className="text-blue-600" size={20} /> Multi-Source Technical Skills Matrix
              </h3>
              <p className="text-xs text-slate-500">Cross-verified evidence combined from CV, Experience, Projects, and GitHub.</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-700">
                {profileSkillMatrix.length} Saved Technical Skills
              </span>
              <button
                type="button"
                onClick={() => setShowSkillMatrixDetails((current) => !current)}
                className="inline-flex items-center gap-1 rounded-lg border border-blue-200 bg-white px-3 py-1.5 text-xs font-bold text-blue-700 hover:bg-blue-50"
              >
                <Eye size={14} /> {showSkillMatrixDetails ? 'Hide Details' : 'Details'}
              </button>
            </div>
          </div>

          {showSkillMatrixDetails && <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs font-bold uppercase tracking-wider text-slate-500 bg-slate-50">
                  <th className="py-3 px-4">Skill</th>
                  <th className="py-3 px-4 text-center">CV Evidence</th>
                  <th className="py-3 px-4 text-center">Experience</th>
                  <th className="py-3 px-4 text-center">Projects</th>
                  <th className="py-3 px-4 text-center">Portfolio</th>
                  <th className="py-3 px-4 text-center">LinkedIn</th>
                  <th className="py-3 px-4 text-center">GitHub Verification</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {displayedProfileSkillMatrix.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-bold text-slate-800 flex items-center gap-2">
                      <Cpu size={15} className="text-indigo-600 shrink-0" />
                      {item.skill}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {item.cv_evidence ? <span className="inline-flex items-center text-green-600 font-bold">✓</span> : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {item.experience_evidence ? <span className="inline-flex items-center text-green-600 font-bold">✓</span> : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {item.projects_evidence ? <span className="inline-flex items-center text-green-600 font-bold">✓</span> : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {item.portfolio_evidence && item.portfolio_url ? (
                        <a href={item.portfolio_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-blue-700 hover:underline" title="Portfolio link provided">
                          <ExternalLink size={13} /> Available
                        </a>
                      ) : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {item.linkedin_evidence && item.linkedin_url ? (
                        <a href={item.linkedin_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-blue-700 hover:underline" title="LinkedIn profile link provided">
                          <ExternalLink size={13} /> Available
                        </a>
                      ) : <span className="text-slate-300">—</span>}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {item.github_evidence ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-bold text-green-700 border border-green-200">
                          <CheckCircle2 size={12} /> Verified
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500">
                          Not Verified
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {item.github_details ? (
                        <button
                          type="button"
                          onClick={() => setSelectedSkillDrillDown(item.github_details)}
                          className="inline-flex items-center gap-1 rounded-lg border border-blue-200 bg-blue-50/50 px-2.5 py-1 text-xs font-bold text-blue-700 hover:bg-blue-100 transition"
                        >
                          <Eye size={13} /> View Evidence
                        </button>
                      ) : (
                        <span className="text-xs text-slate-400">CV Claim Only</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {profileSkillMatrix.length > 32 && (
              <button
                type="button"
                onClick={() => setShowAllSkillMatrix((current) => !current)}
                className="mt-3 w-full rounded-lg border border-blue-200 py-2 text-xs font-bold text-blue-700 hover:bg-blue-50"
              >
                {showAllSkillMatrix ? 'Show less' : `See more (${profileSkillMatrix.length - 32})`}
              </button>
            )}
          </div>}
        </section>
      )}

      {/* GitHub Evidence Section */}
      {user.role === 'candidate' && (
        <section className="rounded-2xl border border-slate-200 bg-slate-50 p-5 sm:p-7 space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-slate-200 pb-4">
            <div>
              <h4 className="flex items-center gap-2 text-lg font-bold text-slate-900">
                <Github size={20} className="text-slate-900" /> Verified GitHub Evidence & Historical Snapshots
              </h4>
              <p className="mt-1 text-xs text-slate-500">
                Public repository facts retrieved strictly from GitHub API. Snapshots are persistent and never overwritten.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button type="button" onClick={verifyPortfolio} disabled={portfolioLoading || !form.portfolioUrl.trim()}
                className="inline-flex items-center gap-1.5 rounded-lg border border-violet-200 bg-violet-50 px-3 py-2 text-xs font-bold text-violet-700 hover:bg-violet-100 disabled:opacity-50">
                {portfolioLoading ? <Loader2 className="animate-spin" size={14} /> : <ExternalLink size={14} />}
                {portfolioLoading ? 'Checking portfolio...' : 'Collect portfolio evidence'}
              </button>
              {portfolioEvidence?.verification_status === 'verified_content' && <span className="text-xs font-semibold text-green-700">Portfolio content verified · {(portfolioEvidence.matched_skills || []).length} skill matches</span>}
              {portfolioError && <span className="text-xs font-semibold text-red-600">{portfolioError}</span>}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={openHistory}
                className="flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 shadow-sm"
              >
                <History size={15} /> Evidence History
              </button>
              <button
                type="button"
                onClick={verifyGithub}
                disabled={githubLoading || !form.githubUrl.trim()}
                className="flex items-center gap-1.5 rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-50 shadow-sm"
              >
                {githubLoading ? <Loader2 className="animate-spin" size={15} /> : <Github size={15} />}
                Refresh GitHub Scan
              </button>
            </div>
          </div>

          {githubEvidence?.latest_refresh_failed && (
            <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-amber-900 text-sm flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle size={18} className="text-amber-700 shrink-0" />
                <span>
                  <strong>Latest refresh failed</strong>: {githubEvidence.refresh_failure_reason || 'GitHub API unavailable/rate-limited'}. Showing last successfully verified snapshot from {githubEvidence.last_verified_at ? new Date(githubEvidence.last_verified_at).toLocaleDateString() : 'earlier'}.
                </span>
              </div>
            </div>
          )}

          {githubError && (
            <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700 border border-red-200">
              {githubError}
            </p>
          )}

          {githubEvidence?.verification_status === 'verified' && (
            <div className="space-y-4">
              <div className="grid gap-3 sm:grid-cols-4">
                <EvidenceMetric label="Status" value="Verified" icon={<ShieldCheck size={16} className="text-green-600" />} />
                <EvidenceMetric label="Repositories" value={githubEvidence.analysis?.repository_count ?? githubEvidence.repositories?.length ?? 0} />
                <EvidenceMetric label="Tested Repos" value={githubEvidence.analysis?.tested_repository_count ?? 0} />
                <div className="rounded-xl bg-white p-3.5 ring-1 ring-slate-200 shadow-sm">
                  <p className="text-xs text-slate-500">Quality Score</p>
                  <p className="mt-1 text-base font-extrabold text-slate-900">{profileQualityScore}/100</p>
                  <button type="button" onClick={() => setShowQualityExplanation(true)} className="mt-2 text-xs font-bold text-blue-700 hover:underline">How is this calculated?</button>
                </div>
              </div>

              {showQualityExplanation && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" role="dialog" aria-modal="true">
                  <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
                    <div className="flex items-start justify-between"><div><h3 className="text-lg font-bold text-slate-900">GitHub Quality Score</h3><p className="mt-1 text-sm text-slate-500">Average evidence score across the repositories inspected by the backend.</p></div><button type="button" onClick={() => setShowQualityExplanation(false)} className="rounded-lg p-2 hover:bg-slate-100"><X size={19} /></button></div>
                    <div className="mt-5 space-y-2 text-sm text-slate-700">
                      <p className="font-semibold">Each repository can receive up to 100 points:</p>
                      <p>README documentation — 30 points</p><p>Automated tests — 25 points</p><p>License — 15 points</p><p>Repository description — 15 points</p><p>Docker or CI/CD workflow — 15 points</p>
                    </div>
                    <div className="mt-5 space-y-2 border-t pt-4">
                      {(githubEvidence.analysis?.selected_repositories || githubEvidence.repositories || []).map((repo) => <div key={repo.repository_url || repo.name} className="flex justify-between rounded-lg bg-slate-50 p-3 text-sm"><span className="font-semibold text-slate-800">{repo.repository_name || repo.name}</span><span className="font-bold text-blue-700">{repo.code_quality?.score ?? 0}/100</span></div>)}
                    </div>
                    <p className="mt-4 rounded-lg bg-blue-50 p-3 text-xs leading-5 text-blue-900">The final value is the arithmetic average of these repository scores. It measures public repository hygiene only and is not a hiring decision.</p>
                  </div>
                </div>
              )}

              {/* Detected Skills with clickable drill-down */}
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Verified Technical Skills (Click for Evidence Drill-Down)
                </p>
                <div className="flex flex-wrap gap-2">
                  {(githubEvidence.skill_evidence || []).filter((item) => isProfileTechnicalSkill(item.skill)).map((item, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setSelectedSkillDrillDown(item)}
                      className="group flex items-center gap-1.5 rounded-xl border border-indigo-200 bg-white px-3 py-1.5 text-xs font-bold text-indigo-800 shadow-sm hover:border-indigo-400 hover:bg-indigo-50/50 transition"
                    >
                      <Cpu size={14} className="text-indigo-600" />
                      <span>{item.skill}</span>
                      <span className="rounded-md bg-indigo-100 px-1.5 py-0.5 text-[10px] text-indigo-700">
                        {Math.round((item.confidence || 0.9) * 100)}%
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Form Section */}
      <form onSubmit={submit} className="space-y-6 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm sm:p-7">
        <h3 className="text-lg font-bold text-slate-900 border-b pb-4">Personal & Professional Information</h3>

        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="Full name" value={form.name} onChange={(v) => update('name', v)} required />
          <Field label="Phone number" value={form.phone} onChange={(v) => update('phone', v)} placeholder="+94 77 123 4567" />
          <Field label="Location" value={form.location} onChange={(v) => update('location', v)} placeholder="Colombo, Sri Lanka" icon={<MapPin size={16} />} />
          {user.role === 'recruiter' ? (
            <Field label="Company" value={form.company} onChange={(v) => update('company', v)} placeholder="Company name" icon={<Building2 size={16} />} />
          ) : (
            <Field label="Professional headline" value={form.headline} onChange={(v) => update('headline', v)} placeholder="Full Stack Developer" />
          )}
        </div>

        {user.role === 'candidate' && (
          <div className="space-y-2">
            <div className="grid gap-5 sm:grid-cols-3">
            <Field label="LinkedIn URL" value={form.linkedinUrl} onChange={(v) => update('linkedinUrl', v)} placeholder="https://linkedin.com/in/..." />
            <Field label="GitHub URL" value={form.githubUrl} onChange={(v) => update('githubUrl', v)} placeholder="https://github.com/username" />
            <Field type="url" label="Portfolio URL" value={form.portfolioUrl} onChange={(v) => update('portfolioUrl', v)} placeholder="https://your-site.com" />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={verifyLinkedinUrl}
                disabled={linkedinLoading || !form.linkedinUrl.trim()}
                className="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-xs font-bold text-blue-700 hover:bg-blue-100 disabled:opacity-50"
              >
                {linkedinLoading ? <Loader2 className="animate-spin" size={14} /> : <CheckCircle size={14} />}
                Verify public LinkedIn URL
              </button>
              <button
                type="button"
                onClick={connectLinkedin}
                disabled={linkedinLoading}
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 hover:bg-slate-100 disabled:opacity-50"
              >
                {linkedinLoading ? <Loader2 className="animate-spin" size={14} /> : <ShieldCheck size={14} />}
                {linkedinLoading ? 'Opening LinkedIn...' : 'Connect official LinkedIn API'}
              </button>
              {linkedinVerification?.verification_status === 'verified_url' && (
                <span className="text-xs font-semibold text-green-700">Public LinkedIn URL validated</span>
              )}
              {linkedinVerification?.verification_status === 'verified' && (
                <span className="text-xs font-semibold text-green-700">Verified on LinkedIn</span>
              )}
              {linkedinError && <span className="text-xs font-semibold text-red-600">{linkedinError}</span>}
              {linkedinHistory.length > 0 && (
                <button type="button" onClick={() => setShowLinkedinHistory((value) => !value)} className="text-xs font-bold text-slate-600 hover:text-slate-900">
                  <History size={13} className="mr-1 inline" />{showLinkedinHistory ? 'Hide' : 'View'} evidence history ({linkedinHistory.length})
                </button>
              )}
            </div>
            {linkedinVerification && linkedinVerification.verification_status !== 'not_connected' && (
              <div className="grid gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 sm:grid-cols-5">
                {[
                  ['Identity', linkedinVerification.identity_verified ? 'Verified' : 'Not verified'],
                  ['Workplace', linkedinVerification.workplace_verified ? 'Verified' : 'Not verified'],
                  ['Education', linkedinVerification.education?.status === 'available' ? 'API evidence' : 'Plus tier required'],
                  ['Skills', 'Not provided by API'],
                  ['Certificates', 'Not provided by API'],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-lg bg-white p-2">
                    <p className="text-[11px] font-bold uppercase text-slate-500">{label}</p>
                    <p className={`mt-1 text-xs font-semibold ${value === 'Verified' || value === 'API evidence' ? 'text-green-700' : 'text-slate-600'}`}>{value}</p>
                  </div>
                ))}
              </div>
            )}
            {showLinkedinHistory && linkedinHistory.length > 0 && (
              <div className="space-y-2 rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-xs font-bold uppercase tracking-wide text-slate-500">Past LinkedIn API evidence</p>
                {linkedinHistory.map((snapshot) => (
                  <div key={snapshot.id || snapshot.verified_at} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 text-xs">
                    <span className="font-semibold text-slate-700">{(snapshot.verified_categories || []).join(', ') || 'Connected — no verification category'}</span>
                    <span className="text-slate-500">{snapshot.verified_at ? new Date(snapshot.verified_at).toLocaleString() : 'Date unavailable'}</span>
                  </div>
                ))}
                <p className="text-[11px] text-amber-700">Cached history is previous LinkedIn API evidence; its timestamp is shown so recruiters can judge freshness.</p>
              </div>
            )}
            <p className="text-xs text-slate-500">Public URL validation needs no API credentials, but it does not prove account ownership or skill claims. Official LinkedIn verification requires API access.</p>
          </div>
        )}

        {user.role === 'candidate' && (
          <StructuredSections
            data={structured}
            token={token}
            onAdded={(section, item) =>
              setStructured((current) => ({ ...current, [section]: [...(current[section] || []).filter((old) => old.id !== item.id), item] }))
            }
          />
        )}

        {user.role === 'candidate' && (
          <div className="space-y-5 rounded-xl border border-slate-100 bg-slate-50/50 p-5">
            <div className="flex flex-col gap-3 border-b border-slate-200 pb-3 sm:flex-row sm:items-center sm:justify-between">
              <h4 className="text-sm font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
                <Code size={16} className="text-blue-600" /> Skills & Competencies (Parsed via Gemini AI)
              </h4>
              <Field label="Experience (years)" value={form.experience} onChange={(v) => update('experience', v)} placeholder="2" type="number" min="0" inline />
            </div>

            <div className="grid gap-5 md:grid-cols-2">
              <div>
                <label className="block text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                  <Cpu size={15} className="text-indigo-600" /> Technical Skills
                </label>
                <input
                  type="text"
                  value={form.technicalSkills}
                  onChange={(e) => update('technicalSkills', e.target.value)}
                  placeholder="React, Python, Docker, SQL, AWS, FastAPI"
                  className="mt-2 w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm outline-none focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100"
                />
                <p className="mt-1 text-xs text-slate-500">Comma-separated technologies & tools</p>
                {techBadges.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {techBadges.map((skill, i) => (
                      <span key={i} className="inline-flex items-center gap-1 rounded-lg bg-indigo-50 border border-indigo-200/80 px-2.5 py-1 text-xs font-semibold text-indigo-700 transition hover:border-indigo-300">
                        {skill}
                        <button
                          type="button"
                          onClick={() => removeTechSkill(skill)}
                          className="ml-0.5 text-indigo-400 hover:text-red-600 hover:bg-red-50 rounded p-0.5 transition"
                          title={`Remove ${skill}`}
                        >
                          <X size={12} />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 flex items-center gap-1.5">
                  <HeartHandshake size={15} className="text-emerald-600" /> Soft Skills
                </label>
                <input
                  type="text"
                  value={form.softSkills}
                  onChange={(e) => update('softSkills', e.target.value)}
                  placeholder="Communication, Team Leadership, Problem Solving"
                  className="mt-2 w-full rounded-xl border border-slate-300 py-2.5 px-3 text-sm outline-none focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100"
                />
                <p className="mt-1 text-xs text-slate-500">Comma-separated interpersonal & work skills</p>
                {softBadges.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {softBadges.map((skill, i) => (
                      <span key={i} className="inline-flex items-center gap-1 rounded-lg bg-emerald-50 border border-emerald-200/80 px-2.5 py-1 text-xs font-semibold text-emerald-700 transition hover:border-emerald-300">
                        {skill}
                        <button
                          type="button"
                          onClick={() => removeSoftSkill(skill)}
                          className="ml-0.5 text-emerald-400 hover:text-red-600 hover:bg-red-50 rounded p-0.5 transition"
                          title={`Remove ${skill}`}
                        >
                          <X size={12} />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-semibold text-slate-700">About / Professional Summary</label>
          <textarea
            value={form.bio}
            onChange={(e) => update('bio', e.target.value)}
            rows="4"
            placeholder="Tell recruiters about your background and achievements..."
            className="mt-2 w-full rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
          />
        </div>

        <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:items-center">
          <button type="submit" className="flex items-center gap-2 rounded-xl bg-blue-600 px-6 py-3 font-bold text-white shadow-sm hover:bg-blue-700 transition">
            <Save size={18} /> Save Profile
          </button>
          {saved && <span className="text-sm font-semibold text-emerald-600">Profile saved successfully.</span>}
        </div>
      </form>

      {/* Evidence Drill-Down Modal */}
      {selectedSkillDrillDown && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in duration-150">
            <div className="flex items-start justify-between border-b pb-4">
              <div>
                <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-bold text-indigo-700 uppercase tracking-wide">
                  Verified Skill Evidence
                </span>
                <h3 className="text-xl font-extrabold text-slate-900 mt-1 flex items-center gap-2">
                  <Cpu className="text-indigo-600" size={22} />
                  {selectedSkillDrillDown.skill}
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedSkillDrillDown(null)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
              >
                <X size={20} />
              </button>
            </div>

            <div className="mt-4 space-y-4">
              <div>
                <p className="text-xs font-bold uppercase text-slate-500">Repository</p>
                <p className="text-sm font-bold text-slate-900 mt-0.5 flex items-center gap-1.5">
                  <FolderGit2 size={16} className="text-blue-600" />
                  {selectedSkillDrillDown.repository || (selectedSkillDrillDown.repositories || []).join(', ') || 'Public Repositories'}
                </p>
              </div>

              <div>
                <p className="text-xs font-bold uppercase text-slate-500 mb-2">Verified Findings</p>
                <div className="space-y-2">
                  {(selectedSkillDrillDown.evidence || []).map((finding, idx) => (
                    <div key={idx} className="flex items-start gap-2.5 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
                      <CheckCircle2 size={16} className="text-green-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-slate-900 uppercase tracking-wider text-[10px] block">
                          {finding.type || 'Finding'}
                        </span>
                        <span>{finding.finding || finding.value || String(finding)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2 border-t">
                <div className="rounded-lg bg-slate-50 p-2.5">
                  <p className="text-[10px] font-bold uppercase text-slate-500">Verification Source</p>
                  <p className="text-xs font-bold text-slate-800 mt-0.5">GitHub REST API</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-2.5">
                  <p className="text-[10px] font-bold uppercase text-slate-500">Confidence</p>
                  <p className="text-xs font-bold text-indigo-700 mt-0.5">
                    {Math.round((selectedSkillDrillDown.confidence || 0.95) * 100)}%
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedSkillDrillDown(null)}
                className="rounded-xl bg-slate-900 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Snapshot History Modal */}
      {showHistoryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
          <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <History className="text-blue-600" size={20} /> GitHub Evidence Snapshots Timeline
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Every scan is immutable and preserved to track skill progression over time.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowHistoryModal(false)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
              >
                <X size={20} />
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {snapshots.map((snap, i) => (
                <div key={snap.id || i} className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-sm">
                      {snap.scanned_at ? new Date(snap.scanned_at).toLocaleString() : 'Recent Snapshot'}
                    </span>
                    <span className="rounded-full bg-blue-100 text-blue-800 px-2.5 py-0.5 text-[11px] font-bold">
                      Snapshot ID: {(snap.id || '').slice(0, 8)}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs text-slate-600">
                    <div>
                      <span className="font-semibold">Repositories:</span> {snap.repositories?.length || snap.analysis?.repository_count || 0}
                    </div>
                    <div>
                      <span className="font-semibold">Quality:</span> {snap.analysis?.code_quality_score ?? snap.raw_analysis?.code_quality_score ?? 0}/100
                    </div>
                    <div>
                      <span className="font-semibold">Skills Detected:</span> {snap.detected_skills?.length || 0}
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {(snap.detected_skills || []).map((sk) => (
                      <span key={sk} className="rounded-md bg-white border border-slate-200 px-2 py-0.5 text-[11px] font-medium text-slate-700">
                        {sk}
                      </span>
                    ))}
                  </div>
                </div>
              ))}

              {!snapshots.length && (
                <p className="text-center py-6 text-sm text-slate-500">No snapshots recorded yet. Run a GitHub verification scan.</p>
              )}
            </div>

            {snapshots.length >= 2 && (
              <div className="mt-6 border-t pt-4 flex items-center justify-between">
                <p className="text-xs text-slate-500">Compare progression across snapshots:</p>
                <button
                  type="button"
                  onClick={() => {
                    setShowHistoryModal(false);
                    setShowCompareModal(true);
                    runComparison();
                  }}
                  className="rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 transition flex items-center gap-1.5"
                >
                  <GitPullRequest size={14} /> Compare Snapshots
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Snapshot Compare Modal */}
      {showCompareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4">
          <div className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b pb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <GitPullRequest className="text-indigo-600" size={20} /> Historical Snapshot Comparison
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Observe repository, technology, and test evidence changes over time.</p>
              </div>
              <button
                type="button"
                onClick={() => setShowCompareModal(false)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
              >
                <X size={20} />
              </button>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-600">Base / Earlier Snapshot</label>
                <select
                  value={compareFromId}
                  onChange={(e) => setCompareFromId(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs bg-white"
                >
                  {snapshots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.scanned_at ? new Date(s.scanned_at).toLocaleDateString() : s.id} (ID: {s.id.slice(0, 6)})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-bold text-slate-600">Target / Later Snapshot</label>
                <select
                  value={compareToId}
                  onChange={(e) => setCompareToId(e.target.value)}
                  className="mt-1 w-full rounded-xl border border-slate-300 p-2 text-xs bg-white"
                >
                  {snapshots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.scanned_at ? new Date(s.scanned_at).toLocaleDateString() : s.id} (ID: {s.id.slice(0, 6)})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-3 flex justify-end">
              <button
                type="button"
                onClick={runComparison}
                className="rounded-lg bg-indigo-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-indigo-700 transition"
              >
                Re-Compare
              </button>
            </div>

            {compareData && (
              <div className="mt-4 space-y-3">
                <div className="rounded-xl border border-green-200 bg-green-50 p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-green-800">Newly Detected Skills</p>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {(compareData.changes?.new_skills_detected || []).length > 0 ? (
                      compareData.changes.new_skills_detected.map((sk) => (
                        <span key={sk} className="rounded-md bg-white border border-green-300 px-2 py-0.5 text-xs font-bold text-green-800">
                          + {sk}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-green-700">No new skills detected between these dates</span>
                    )}
                  </div>
                </div>

                <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-blue-800">New Evidence & Capabilities Added</p>
                  <ul className="mt-1 list-disc list-inside text-xs text-blue-900 space-y-1">
                    {(compareData.changes?.new_evidence || []).length > 0 ? (
                      compareData.changes.new_evidence.map((ev, i) => <li key={i}>{ev}</li>)
                    ) : (
                      <li>No new file/test markers added</li>
                    )}
                  </ul>
                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-700">New Repositories</p>
                  <p className="text-xs text-slate-600 mt-1">
                    {(compareData.changes?.new_repositories || []).join(', ') || 'No new repositories created.'}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function EvidenceMetric({ label, value, icon }) {
  return (
    <div className="rounded-xl bg-white p-3.5 ring-1 ring-slate-200 shadow-sm">
      <p className="text-xs text-slate-500 flex items-center justify-between">
        {label}
        {icon}
      </p>
      <p className="mt-1 text-base font-extrabold text-slate-900">{value}</p>
    </div>
  );
}

function StructuredSections({ data, token, onAdded }) {
  const empty = {
    languages: { language: '', speaking_level: '', reading_level: '', writing_level: '' },
    projects: { name: '', description: '', technologies: '' },
    education: { qualification: '', institution: '', field: '', start_year: '', end_year: '', grade: '' },
  };
  const [forms, setForms] = useState(empty);
  const [open, setOpen] = useState('');
  const [error, setError] = useState('');
  const [expandedLists, setExpandedLists] = useState({ projects: false, cv_analyses: false });
  const add = async (section) => {
    setError('');
    try {
      const raw = forms[section];
      const payload = { ...raw };
      if (section === 'projects') payload.technologies = raw.technologies.split(',').map((item) => item.trim()).filter(Boolean);
      if (section === 'education') {
        payload.start_year = raw.start_year ? Number(raw.start_year) : null;
        payload.end_year = raw.end_year ? Number(raw.end_year) : null;
      }
      const item = await apiRequest(`/api/candidates/me/${section}?token=${encodeURIComponent(token)}`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      onAdded(section, item);
      setForms((current) => ({ ...current, [section]: empty[section] }));
      setOpen('');
    } catch (err) {
      setError(err.message);
    }
  };
  const sections = [
    {
      key: 'languages',
      title: 'Languages',
      icon: <Languages size={18} />,
      empty: 'No languages extracted yet.',
      render: (item) => (
        <>
          <b>{item.language}</b>
          <span>
            {[item.speaking_level && `Speaking: ${item.speaking_level}`, item.reading_level && `Reading: ${item.reading_level}`, item.writing_level && `Writing: ${item.writing_level}`]
                .filter(Boolean)
                .join(' · ') ||
              'Level not provided'}
          </span>
        </>
      ),
    },
    {
      key: 'projects',
      title: 'Projects',
      icon: <FolderGit2 size={18} />,
      empty: 'No projects extracted yet.',
      render: (item) => (
        <>
          <b>{item.name}</b>
          <span>{item.description || item.candidate_contribution || 'No description provided'}</span>
          <small>{(item.technologies || []).join(', ')}</small>
        </>
      ),
    },
    {
      key: 'education',
      title: 'Education details',
      icon: <GraduationCap size={18} />,
      empty: 'No education details extracted yet.',
      render: (item) => (
        <>
          <b>{item.degree || item.qualification}</b>
          <span>{[item.field, item.institution].filter(Boolean).join(' · ') || 'Institution not provided'}</span>
          <small>
            {[item.start_year, item.end_year].filter(Boolean).join(' – ')} {item.grade ? ` · ${item.grade}` : ''}
          </small>
        </>
      ),
    },
    {
      key: 'cv_analyses',
      title: 'CV analyses',
      icon: <History size={18} />,
      empty: 'No CV analysis history yet.',
      render: (item) => (
        <>
          <b>{item.file_name}</b>
          <span className="capitalize">{String(item.parsing_status || 'pending').replace('_', ' ')}</span>
          <small>
            {item.parser_model || item.parser || 'Local extraction'}
            {item.parsed_at ? ` · ${new Date(item.parsed_at).toLocaleDateString()}` : ''}
          </small>
        </>
      ),
    },
  ];
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {sections.map((section) => (
        <section key={section.key} className="rounded-xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between">
            <h4 className="flex items-center gap-2 font-bold text-slate-900">
              {section.icon}
              {section.title}
            </h4>
            {section.key === 'cv_analyses' ? (
              <button
                type="button"
                onClick={() => setExpandedLists((current) => ({ ...current, cv_analyses: !current.cv_analyses }))}
                className="rounded-lg border border-indigo-200 px-3 py-1 text-xs font-bold text-indigo-700"
              >
                {expandedLists.cv_analyses ? 'Hide history' : `View history (${(data?.cv_analyses || []).length})`}
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setError('');
                  setOpen(open === section.key ? '' : section.key);
                }}
                className="rounded-lg border border-blue-200 px-3 py-1 text-xs font-bold text-blue-700"
              >
                {open === section.key ? 'Cancel' : '+ Add manually'}
              </button>
            )}
          </div>
          {open === section.key && (
            <ManualRecordForm
              section={section.key}
              value={forms[section.key]}
              setValue={(value) => setForms((current) => ({ ...current, [section.key]: value }))}
              onSave={() => add(section.key)}
              error={error}
            />
          )}
          <div className="mt-3 space-y-2">
            {section.key === 'cv_analyses' && !expandedLists.cv_analyses ? (
              <p className="text-sm text-slate-400">CV analysis records are hidden. Click “View history” to inspect them.</p>
            ) : (data?.[section.key] || []).length ? (
              (section.key === 'projects' && !expandedLists.projects ? data[section.key].slice(0, 2) : data[section.key]).map((item, index) => (
                <div key={item.id || index} className="flex flex-col rounded-lg bg-slate-50 p-3 text-sm text-slate-600 ring-1 ring-slate-100">
                  {section.render(item)}
                  <small className="mt-1 text-blue-600">
                    {(item.sources || [item.source])
                      .filter(Boolean)
                      .map((source) => (source === 'cv_gemini' ? 'CV · Gemini' : source === 'candidate_manual' ? 'Manual' : source))
                      .join(' + ')}
                  </small>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-400">{section.empty}</p>
            )}
            {section.key === 'projects' && (data?.projects || []).length > 2 && (
              <button type="button" onClick={() => setExpandedLists((current) => ({ ...current, projects: !current.projects }))} className="w-full rounded-lg border border-blue-200 py-2 text-sm font-bold text-blue-700 hover:bg-blue-50">
                {expandedLists.projects ? 'Show less' : `See more (${data.projects.length - 2})`}
              </button>
            )}
          </div>
        </section>
      ))}
    </div>
  );
}

/**
 * Form allowing candidate to manually input structured credentials (languages, projects, education).
 */
function ManualRecordForm({ section, value, setValue, onSave, error }) {
  const LANGUAGE_OPTIONS = ['English', 'Sinhala', 'Tamil'];
  const PROFICIENCY_OPTIONS = ['Basic', 'Moderate', 'Fluent'];
  const field = (name, placeholder, type = 'text') => (
    <input
      type={type}
      value={value[name] ?? ''}
      onChange={(e) => setValue({ ...value, [name]: e.target.value })}
      placeholder={placeholder}
      className="rounded-lg border border-slate-300 bg-white p-2 text-sm"
    />
  );
  const select = (name, label, options) => (
    <label className="text-xs font-semibold text-slate-600">
      {label}
      <select
        required
        value={value[name] ?? ''}
        onChange={(e) => setValue({ ...value, [name]: e.target.value })}
        className="mt-1 w-full rounded-lg border border-slate-300 bg-white p-2 text-sm text-slate-800"
      >
        <option value="" disabled>Select {label.toLowerCase()}</option>
        {options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    </label>
  );
  return (
    <div className="mt-3 grid gap-2 rounded-lg bg-blue-50 p-3">
      {section === 'languages' && (
        <>
          {select('language', 'Language', LANGUAGE_OPTIONS)}
          <div className="grid gap-2 sm:grid-cols-3">
            {select('speaking_level', 'Speaking', PROFICIENCY_OPTIONS)}
            {select('reading_level', 'Reading', PROFICIENCY_OPTIONS)}
            {select('writing_level', 'Writing', PROFICIENCY_OPTIONS)}
          </div>
        </>
      )}
      {section === 'projects' && (
        <>
          {field('name', 'Project name')}
          {field('description', 'Description')}
          {field('technologies', 'Technologies, comma separated')}
        </>
      )}
      {section === 'education' && (
        <>
          {field('qualification', 'Qualification / degree')}
          {field('institution', 'Institution')}
          {field('field', 'Field of study')}
          <div className="grid grid-cols-2 gap-2">
            {field('start_year', 'Start year', 'number')}
            {field('end_year', 'End year', 'number')}
          </div>
          {field('grade', 'GPA / grade / class')}
        </>
      )}
      {error && <p className="text-xs font-semibold text-red-700">{error}</p>}
      <button type="button" onClick={onSave} className="rounded-lg bg-blue-600 px-3 py-2 text-sm font-bold text-white">
        Save structured record
      </button>
    </div>
  );
}

/**
 * Reusable input field component with icon, label, and inline support.
 */
function Field({ label, value, onChange, placeholder, required, icon, type = 'text', min, inline = false }) {
  if (inline) {
    return (
      <div className="flex items-center gap-2">
        <label className="text-xs font-semibold text-slate-600 whitespace-nowrap">{label}</label>
        <input
          type={type}
          min={min}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-20 rounded-lg border border-slate-300 py-1 px-2 text-sm outline-none focus:border-blue-500"
        />
      </div>
    );
  }
  return (
    <div>
      <label className="block text-sm font-semibold text-slate-700">{label}</label>
      <div className="relative mt-2">
        {icon && <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">{icon}</span>}
        <input
          type={type}
          min={min}
          required={required}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full rounded-xl border border-slate-300 py-3 pr-3 text-sm outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-100 ${
            icon ? 'pl-10' : 'pl-3'
          }`}
        />
      </div>
    </div>
  );
}

