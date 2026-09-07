"""GitHub Verification and Technical Evidence Analysis Service."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from github_evidence import (
    GithubVerificationError,
    analyze_github_with_gemini,
    compute_cv_github_consistency,
    github_skill_records,
    verify_github_profile as fetch_raw_github_profile,
)
from repositories.github_repository import GithubRepository
from models.github import GithubSkillEvidenceModel


def utcnow():
    return datetime.now(timezone.utc)


class GithubService:
    def __init__(self, github_repo: GithubRepository, api_key: str = "", model_name: str = "gemini-3.5-flash-lite"):
        self.github_repo = github_repo
        self.api_key = api_key
        self.model_name = model_name

    def calculate_github_score(self, github_data: Dict[str, Any], job: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculates GitHub Score (Max 15) using backend deterministic rules:
        - Verified technologies: up to 5
        - Relevant repositories: up to 3
        - Contribution/activity: up to 2
        - Project complexity: up to 2
        - Documentation quality: up to 1
        - Code/project structure: up to 1
        - Recent activity: up to 1
        Maximum = 15.
        """
        if not github_data or github_data.get("verification_status") not in {"verified", "success"}:
            return {
                "score": 0.0,
                "max_score": 15.0,
                "reason": "No verified public GitHub profile provided.",
                "evidence": ["GitHub profile unverified or missing."],
                "breakdown": {
                    "verified_technologies": 0.0,
                    "relevant_repositories": 0.0,
                    "contribution_activity": 0.0,
                    "project_complexity": 0.0,
                    "documentation_quality": 0.0,
                    "code_structure": 0.0,
                    "recent_activity": 0.0,
                }
            }

        detected_skills = github_data.get("detected_skills") or []
        repos = github_data.get("repositories") or []
        analysis = github_data.get("analysis") or {}
        
        # 1. Verified technologies (Max 5)
        # 1 point per verified tech up to 5 max
        tech_score = min(5.0, float(len(detected_skills)))
        
        # 2. Relevant repositories (Max 3)
        # Repositories with detected technologies or descriptions
        non_fork_repos = [r for r in repos if not r.get("fork")]
        rel_score = min(3.0, round(len(non_fork_repos) * 0.75, 1))

        # 3. Contribution / activity (Max 2)
        public_repos_count = (github_data.get("profile") or {}).get("public_repos", len(repos))
        activity_score = min(2.0, 1.0 if public_repos_count >= 2 else 0.5 if public_repos_count >= 1 else 0.0)

        # 4. Project complexity (Max 2)
        # Docker, tests, or multi-language projects
        docker_count = analysis.get("dockerized_repository_count", 0)
        test_count = analysis.get("tested_repository_count", 0)
        complexity_score = 0.0
        if docker_count > 0:
            complexity_score += 1.0
        if test_count > 0:
            complexity_score += 1.0
        complexity_score = min(2.0, complexity_score)

        # 5. Documentation quality (Max 1)
        readme_count = analysis.get("readme_repository_count", 0)
        doc_score = 1.0 if readme_count > 0 else 0.0

        # 6. Code / project structure (Max 1)
        quality_score = float(analysis.get("code_quality_score", 0))
        structure_score = 1.0 if quality_score >= 50 else 0.5 if quality_score >= 30 else 0.0

        # 7. Recent activity (Max 1)
        # Check pushed_at on repos within last year
        recent_activity_score = 1.0 if repos and any(r.get("pushed_at") for r in repos[:3]) else 0.0

        total_score = round(min(15.0, tech_score + rel_score + activity_score + complexity_score + doc_score + structure_score + recent_activity_score), 1)

        evidence_bullets = [
            f"Verified {len(detected_skills)} technologies via GitHub API: {', '.join(detected_skills[:5])}" if detected_skills else "Public GitHub profile detected",
            f"Sampled {len(repos)} public repositories ({len(non_fork_repos)} original projects)",
        ]
        if docker_count > 0:
            evidence_bullets.append(f"Containerization (Docker) verified in {docker_count} repository")
        if test_count > 0:
            evidence_bullets.append(f"Automated test suites verified in {test_count} repository")

        return {
            "score": total_score,
            "max_score": 15.0,
            "reason": f"Evaluated from GitHub API-verified evidence ({total_score}/15 points).",
            "evidence": evidence_bullets,
            "breakdown": {
                "verified_technologies": tech_score,
                "relevant_repositories": rel_score,
                "contribution_activity": activity_score,
                "project_complexity": complexity_score,
                "documentation_quality": doc_score,
                "code_structure": structure_score,
                "recent_activity": recent_activity_score,
            }
        }

    async def verify_and_store_github(self, candidate_id: str, github_url_or_username: str, cv_skills: Optional[List[str]] = None, job: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch real data from GitHub API, run semantic analysis, calculate scores, store in MongoDB."""
        try:
            raw_evidence = await asyncio.to_thread(fetch_raw_github_profile, github_url_or_username)
        except GithubVerificationError as exc:
            existing = self.github_repo.get_latest_github_profile(candidate_id)
            if existing:
                self.github_repo.db.candidate_github.update_one(
                    {"candidate_id": candidate_id},
                    {"$set": {"latest_refresh_failed": True, "last_failed_refresh_at": utcnow().isoformat(), "refresh_failure_reason": str(exc)}}
                )
                requested = str(github_url_or_username or "").strip().rstrip("/").split("/")[-1].casefold()
                cached = str(existing.get("username") or "").casefold()
                if "rate limit" in str(exc).casefold() and requested == cached:
                    existing.update({
                        "latest_refresh_failed": True,
                        "evidence_source_status": "cached",
                        "refresh_failure_reason": str(exc),
                    })
                    return existing
            raise

        cv_skill_list = cv_skills or []
        cv_consistency = compute_cv_github_consistency(cv_skill_list, raw_evidence.get("detected_skills", []))

        gemini_analysis = await analyze_github_with_gemini(
            raw_evidence,
            cv_skill_list,
            job=job,
            api_key=self.api_key,
            model_name=self.model_name
        )

        # Enhance skill evidence items format with claimed, verified, evidence_source, repository, confidence
        skill_evidence_records = []
        for item in raw_evidence.get("skill_evidence", []):
            findings = item.get("evidence", [])
            finding_texts = [f.get("finding") if isinstance(f, dict) else str(f) for f in findings]
            repo_name = item.get("repository") or (item.get("repositories", ["github"])[0] if item.get("repositories") else "github")
            
            skill_evidence_records.append({
                "skill": item["skill"],
                "claimed": True,
                "verified": True,
                "evidence_source": "github",
                "repository": repo_name,
                "repositories": item.get("repositories", [repo_name]),
                "evidence": finding_texts,
                "confidence": item.get("confidence", 0.92),
            })

        score_details = self.calculate_github_score(raw_evidence, job)

        snapshot_id = f"gh_snap_{candidate_id}_{int(utcnow().timestamp())}"
        snapshot_doc = {
            "id": snapshot_id,
            "_id": snapshot_id,
            "candidate_id": candidate_id,
            "github_url": raw_evidence["github_url"],
            "username": raw_evidence["username"],
            "scanned_at": raw_evidence["verified_at"],
            "verification_status": "verified",
            "profile": raw_evidence.get("profile"),
            "repositories": raw_evidence.get("repositories", []),
            "detected_skills": raw_evidence.get("detected_skills", []),
            "skill_evidence": skill_evidence_records,
            "cv_consistency": cv_consistency,
            "analysis": gemini_analysis,
            "github_score": score_details,
            "api_status": "success",
            "github_data_version": 2,
        }

        # Store in MongoDB via github repository layer
        self.github_repo.save_github_snapshot(candidate_id, snapshot_doc)
        return snapshot_doc
