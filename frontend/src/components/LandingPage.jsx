import React, { useMemo, useState } from 'react';
import { ArrowRight, Briefcase, CheckCircle2, MapPin, Search, ShieldCheck, Sparkles } from 'lucide-react';
import BrandLogo from './BrandLogo';

export default function LandingPage({ jobs = [], loading = false, onSignIn, onCreateAccount, onApply }) {
  const [query, setQuery] = useState('');
  const filteredJobs = useMemo(() => {
    const value = query.trim().toLowerCase();
    return jobs.filter((job) => !value || [job.title, job.company, job.location, job.type, job.skills]
      .some((field) => String(field || '').toLowerCase().includes(value)));
  }, [jobs, query]);

  return <main className="min-h-screen bg-slate-50 text-slate-900">
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
      <div className="mx-auto grid max-w-7xl grid-cols-[auto_1fr_auto] items-center gap-2 px-3 py-4 sm:gap-6 sm:px-8">
        <BrandLogo />
        <nav className="flex items-center justify-end sm:justify-center" aria-label="Main navigation">
          <a href="#jobs" className="group relative flex items-center gap-2 px-2 py-2 text-sm font-bold text-slate-600 transition hover:text-blue-700 sm:px-3">
            <Briefcase size={17} className="hidden text-slate-400 transition group-hover:text-blue-600 sm:block" />
            <span>Find jobs</span>
            <span className="absolute inset-x-2 bottom-0 h-0.5 origin-left scale-x-0 rounded-full bg-blue-600 transition-transform group-hover:scale-x-100" />
          </a>
        </nav>
        <div className="flex shrink-0 items-center gap-1 border-l border-slate-200 pl-2 sm:gap-3 sm:pl-4">
          <button onClick={onSignIn} className="rounded-xl px-4 py-2.5 text-sm font-bold text-slate-700 transition hover:bg-slate-100">Sign in</button>
          <button onClick={onCreateAccount} className="rounded-xl bg-blue-600 px-3 py-2.5 text-sm font-bold text-white shadow-lg shadow-blue-600/20 transition hover:bg-blue-700 sm:px-4">Create account</button>
        </div>
      </div>
    </header>

    <section className="relative flex min-h-[calc(100svh-73px)] overflow-hidden bg-slate-950">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(37,99,235,.32),transparent_32%),radial-gradient(circle_at_85%_30%,rgba(79,70,229,.25),transparent_30%)]" />
      <div className="relative mx-auto grid w-full max-w-7xl flex-1 content-center gap-10 px-5 py-12 sm:px-8 sm:py-16 lg:grid-cols-[1.08fr_.92fr] lg:items-center lg:gap-14 lg:py-20">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-400/30 bg-blue-400/10 px-3 py-1.5 text-sm font-semibold text-blue-200 lg:px-4 lg:py-2 lg:text-base"><Sparkles size={18}/> AI-powered career matching</div>
          <h1 className="mt-6 text-4xl font-black leading-[1.06] tracking-[-0.035em] text-white sm:text-6xl lg:text-7xl">Find work that fits your skills, not just your CV.</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300 lg:text-xl lg:leading-9">Explore open roles before creating an account. When you find the right opportunity, sign in to analyze your match and apply.</p>
        </div>
        <div className="w-full justify-self-end rounded-3xl border border-white/10 bg-white/[0.08] p-6 shadow-2xl shadow-black/20 backdrop-blur-sm lg:max-w-xl lg:p-8">
          <p className="text-sm font-bold uppercase tracking-widest text-blue-200 lg:text-base">A clearer way to apply</p>
          <div className="mt-6 space-y-4 lg:mt-8 lg:space-y-5">
            {['Discover verified opportunities', 'Compare your skills with each role', 'Apply with a stronger, focused profile'].map((item) => <div key={item} className="flex items-center gap-3 rounded-2xl bg-white/10 p-4 text-white lg:gap-4 lg:p-5"><CheckCircle2 className="shrink-0 text-cyan-300" size={24}/><span className="font-semibold lg:text-lg">{item}</span></div>)}
          </div>
          <div className="mt-6 flex items-center gap-3 border-t border-white/10 pt-5 text-sm text-slate-300 lg:mt-8 lg:pt-7 lg:text-base"><ShieldCheck size={21} className="text-blue-300"/> Your information stays protected.</div>
        </div>
      </div>
    </section>

    <section id="jobs" className="mx-auto min-h-screen max-w-7xl scroll-mt-[73px] px-5 py-16 sm:px-8 sm:py-20">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div><p className="text-sm font-bold uppercase tracking-widest text-blue-600">Open opportunities</p><h2 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">Available jobs</h2><p className="mt-3 text-slate-500">Search by role, company, location, or skill.</p></div>
        <div className="relative w-full lg:max-w-md"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={20}/><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search available jobs" className="h-14 w-full rounded-2xl border border-slate-300 bg-white pl-12 pr-4 text-sm shadow-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"/></div>
      </div>

      <div className="mt-9 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {loading && [1,2,3].map((item) => <div key={item} className="h-72 animate-pulse rounded-2xl bg-slate-200" />)}
        {!loading && filteredJobs.map((job) => <article key={job.id} className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-xl hover:shadow-slate-200/60">
          <div className="flex items-start justify-between gap-4"><div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><Briefcase size={23}/></div><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">Open</span></div>
          <h3 className="mt-5 text-xl font-extrabold group-hover:text-blue-700">{job.title}</h3>
          <p className="mt-1 font-semibold text-slate-500">{job.company}</p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold text-slate-600"><span className="flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1.5"><MapPin size={13}/>{job.location}</span><span className="rounded-full bg-slate-100 px-2.5 py-1.5">{job.type}</span><span className="rounded-full bg-amber-50 px-2.5 py-1.5 text-amber-700">{Number(job.experience || 0)}+ years</span></div>
          <p className="mt-4 line-clamp-2 text-sm leading-6 text-slate-500">{job.description || 'Explore this opportunity and see how your experience matches the role.'}</p>
          <button onClick={() => onApply(job)} className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-3 font-bold text-white transition hover:bg-blue-600">Sign in to apply <ArrowRight size={17}/></button>
        </article>)}
      </div>
      {!loading && !filteredJobs.length && <div className="mt-9 rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center text-slate-500">No jobs match your search. Try another title, skill, or location.</div>}
    </section>

    <footer className="border-t border-slate-200 bg-white"><div className="mx-auto flex max-w-7xl flex-col gap-4 px-5 py-8 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-8"><BrandLogo/><p>Smarter matching for candidates and recruiters.</p></div></footer>
  </main>;
}
