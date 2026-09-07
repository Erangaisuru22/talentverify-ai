"""Verified, structured GitHub evidence collected from GitHub's public REST API."""

import base64
import json
import os
import re
import shutil
import ssl
import subprocess
import uuid
from collections import Counter
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from gemini_rest import generate_json as generate_gemini_json


class GithubVerificationError(Exception):
    """A safe, user-facing verification failure."""


_USE_WINDOWS_TLS_FALLBACK = False


def utcnow():
    return datetime.now(timezone.utc)


def identifier():
    return str(uuid.uuid4())


def normalize_skill(value: str) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def github_username(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        raise GithubVerificationError("Enter a GitHub profile URL or username.")
    if "://" in value:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"github.com", "www.github.com"}:
            raise GithubVerificationError("Only https://github.com profile URLs are supported.")
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) == 0:
            raise GithubVerificationError("Enter a valid GitHub profile URL.")
        # If user pasted repo URL like https://github.com/user/repo, extract the username
        value = parts[0]
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", value):
        raise GithubVerificationError("The GitHub username is invalid.")
    return value


def _request(path: str, allow_missing=False):
    global _USE_WINDOWS_TLS_FALLBACK
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "TalentVerifyAI/2.0"}
    # GH_TOKEN is also supported by GitHub CLI and many deployment platforms.
    token = (os.getenv("GITHUB_TOKEN", "") or os.getenv("GH_TOKEN", "")).strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if _USE_WINDOWS_TLS_FALLBACK:
        return _curl_request(path, headers, allow_missing)
    try:
        with urlopen(Request(f"https://api.github.com{path}", headers=headers), timeout=12) as response:
            return json.loads(response.read().decode("utf-8")), dict(response.headers)
    except HTTPError as exc:
        if allow_missing and exc.code == 404:
            return None, {}
        if exc.code == 404:
            raise GithubVerificationError("GitHub profile was not found.") from exc
        if exc.code in {403, 429}:
            raise GithubVerificationError("GitHub API rate limit reached. Configure GITHUB_TOKEN or retry later.") from exc
        raise GithubVerificationError(f"GitHub API returned HTTP {exc.code}.") from exc
    except URLError as exc:
        if isinstance(getattr(exc, "reason", None), ssl.SSLCertVerificationError):
            _USE_WINDOWS_TLS_FALLBACK = True
            return _curl_request(path, headers, allow_missing)
        raise GithubVerificationError(f"GitHub connection failed: {getattr(exc, 'reason', exc)}") from exc
    except (TimeoutError, json.JSONDecodeError) as exc:
        raise GithubVerificationError("GitHub could not be reached. Please retry.") from exc


def _curl_request(path, headers, allow_missing=False):
    executable = shutil.which("curl.exe") or shutil.which("curl")
    if not executable:
        raise GithubVerificationError("GitHub TLS validation failed and no secure Windows TLS fallback is available.")
    url = f"https://api.github.com{path}"
    config = [f'url = "{url}"', "silent", "show-error", "fail-with-body", "connect-timeout = 10", "max-time = 20"]
    for name, value in headers.items():
        safe_value = str(value).replace('"', '')
        config.append(f'header = "{name}: {safe_value}"')
    try:
        result = subprocess.run([executable, "--config", "-", "--write-out", "\n%{http_code}"],
                                input="\n".join(config), capture_output=True, text=True, timeout=25, check=False)
        body, _, status_text = result.stdout.rpartition("\n")
        status = int(status_text) if status_text.isdigit() else 0
        if allow_missing and status == 404:
            return None, {}
        if status == 404:
            raise GithubVerificationError("GitHub profile was not found.")
        if status in {403, 429}:
            raise GithubVerificationError("GitHub API rate limit reached. Configure GITHUB_TOKEN or retry later.")
        if result.returncode or not 200 <= status < 300:
            raise GithubVerificationError(f"GitHub API request failed (HTTP {status or 'unknown'}).")
        return json.loads(body), {}
    except GithubVerificationError:
        raise
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise GithubVerificationError("The secure GitHub TLS fallback failed. Please retry.") from exc


TECH_PATTERNS = {
    "FastAPI": {"dependencies": ["fastapi"], "entry_points": ["main.py", "app.py"], "code_keywords": ["FastAPI(", "APIRouter"], "docs": ["fastapi"]},
    "Flask": {"dependencies": ["flask"], "entry_points": ["app.py", "wsgi.py"], "code_keywords": ["Flask(__name__)"], "docs": ["flask"]},
    "Django": {"dependencies": ["django"], "entry_points": ["manage.py", "wsgi.py", "asgi.py"], "code_keywords": ["django.core"], "docs": ["django"]},
    "PyTorch": {"dependencies": ["torch", "torchvision", "torchaudio"], "entry_points": ["train.py", "model.py"], "code_keywords": ["import torch", "nn.Module"], "docs": ["pytorch", "torch"]},
    "TensorFlow": {"dependencies": ["tensorflow", "keras"], "entry_points": ["train.py", "model.py"], "code_keywords": ["import tensorflow", "from tensorflow"], "docs": ["tensorflow", "keras"]},
    "React": {"dependencies": ["react", "react-dom"], "entry_points": ["App.jsx", "App.tsx", "main.jsx", "index.js"], "code_keywords": ["useState", "useEffect", "React."], "docs": ["react"]},
    "Next.js": {"dependencies": ["next"], "entry_points": ["next.config.js", "next.config.mjs", "app/page.tsx", "pages/index.tsx"], "code_keywords": ["next/router", "next/image"], "docs": ["next.js", "nextjs"]},
    "Vue": {"dependencies": ["vue"], "entry_points": ["App.vue", "main.js"], "code_keywords": ["createApp"], "docs": ["vue"]},
    "Angular": {"dependencies": ["@angular/core"], "entry_points": ["angular.json"], "code_keywords": ["@Component"], "docs": ["angular"]},
    "Node.js": {"dependencies": [], "entry_points": ["server.js", "index.js", "package.json"], "code_keywords": [], "docs": ["node.js", "nodejs"]},
    "Express": {"dependencies": ["express"], "entry_points": ["server.js", "app.js", "index.js"], "code_keywords": ["express()"], "docs": ["express"]},
    "Docker": {"files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "Containerfile"], "docs": ["docker"]},
    "Kubernetes": {"files": ["k8s", "helm", "kubernetes"], "docs": ["kubernetes", "k8s"]},
    "MongoDB": {"dependencies": ["pymongo", "motor", "mongoose", "mongodb"], "docs": ["mongodb", "mongo"]},
    "PostgreSQL": {"dependencies": ["psycopg2", "psycopg2-binary", "asyncpg", "pg", "prisma"], "docs": ["postgres", "postgresql"]},
    "Redis": {"dependencies": ["redis", "aioredis", "ioredis"], "docs": ["redis"]},
    "GraphQL": {"dependencies": ["graphql", "apollo-server", "graphene", "strawberry-graphql"], "docs": ["graphql"]},
    "Selenium": {"dependencies": ["selenium"], "docs": ["selenium"]},
    "Playwright": {"dependencies": ["playwright", "@playwright/test"], "files": ["playwright.config.ts", "playwright.config.js"], "docs": ["playwright"]},
    "Pytest": {"dependencies": ["pytest"], "files": ["pytest.ini", "conftest.py"], "docs": ["pytest"]},
    "Jest": {"dependencies": ["jest", "ts-jest"], "files": ["jest.config.js", "jest.config.ts"], "docs": ["jest"]},
    "Vitest": {"dependencies": ["vitest"], "files": ["vitest.config.ts", "vitest.config.js"], "docs": ["vitest"]},
    "Tailwind CSS": {"dependencies": ["tailwindcss"], "files": ["tailwind.config.js", "tailwind.config.ts"], "docs": ["tailwind"]},
    "TypeScript": {"dependencies": ["typescript"], "files": ["tsconfig.json"], "docs": ["typescript"]},
    "Python": {"files": ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py"], "languages": ["Python"]},
    "JavaScript": {"files": ["package.json"], "languages": ["JavaScript"]},
    "CI/CD (GitHub Actions)": {"files": [".github/workflows"], "docs": ["ci/cd", "github actions", "pipeline"]},
}


def _decode_file_content(item):
    if not isinstance(item, dict):
        return ""
    content = item.get("content", "")
    encoding = item.get("encoding", "")
    if encoding == "base64" and content:
        try:
            return base64.b64decode(content).decode("utf-8", errors="ignore")
        except Exception:
            return ""
    return str(content or "")


def _inspect_repo(username, repo):
    owner, name = repo["owner"]["login"], repo["name"]
    slug = f"{quote(owner)}/{quote(name)}"

    def optional(path, default):
        try:
            result, _ = _request(path, allow_missing=True)
            return default if result is None else result
        except GithubVerificationError:
            return default

    limited_evidence = _USE_WINDOWS_TLS_FALLBACK
    languages = ({repo.get("language"): 1} if limited_evidence and repo.get("language") else
                 optional(f"/repos/{slug}/languages", {}))
    readme_obj = None if limited_evidence else optional(f"/repos/{slug}/readme", None)
    contents = [] if limited_evidence else optional(f"/repos/{slug}/contents", [])

    file_names = [str(item.get("name", "")).strip() for item in contents or [] if isinstance(item, dict)]
    file_names_lower = [f.casefold() for f in file_names]

    # Check for test markers
    test_markers = ("test", "tests", "spec", "specs", "pytest.ini", "jest.config.js", "vitest.config.ts")
    has_tests = any(any(marker == f or f.startswith(marker + ".") or marker in f for marker in test_markers) for f in file_names_lower)

    # Check for docker markers
    has_docker = any(f in {"dockerfile", "docker-compose.yml", "docker-compose.yaml", "containerfile"} for f in file_names_lower)

    # Check for CI/CD workflows
    has_workflows = ".github" in file_names_lower or any(f.endswith(".yml") or f.endswith(".yaml") for f in file_names_lower)
    if not limited_evidence and ".github" in file_names_lower:
        workflows = optional(f"/repos/{slug}/contents/.github/workflows", [])
        if workflows and isinstance(workflows, list):
            has_workflows = True

    # Read key dependency files if present
    dependency_text = ""
    for dep_file in ("requirements.txt", "pyproject.toml", "package.json", "Pipfile"):
        if dep_file.casefold() in file_names_lower:
            file_data = optional(f"/repos/{slug}/contents/{dep_file}", None)
            if file_data:
                dependency_text += "\n" + _decode_file_content(file_data).casefold()

    readme_text = ""
    if readme_obj:
        readme_text = _decode_file_content(readme_obj).casefold()

    description_text = str(repo.get("description") or "").casefold()
    topics = [str(t).casefold() for t in (repo.get("topics") or [])]

    # Detect skills and create structured evidence items
    technologies_detected = []
    skill_evidence_items = []
    evidence_records = []

    primary_lang = repo.get("language")
    if primary_lang and primary_lang not in technologies_detected:
        technologies_detected.append(primary_lang)
        skill_evidence_items.append({
            "skill": primary_lang,
            "evidence_source": "github",
            "repository": name,
            "evidence": [{"type": "language", "finding": f"Primary repository language: {primary_lang}"}],
            "verified": True,
            "confidence": 0.98,
        })
        evidence_records.append({"type": "language", "value": primary_lang})

    for tech, rules in TECH_PATTERNS.items():
        findings = []
        # Check dependencies
        for dep in rules.get("dependencies", []):
            if dep.casefold() in dependency_text:
                findings.append({"type": "dependency", "finding": f"{dep} dependency found in project manifest"})
                evidence_records.append({"type": "dependency", "value": dep})
                break

        # Check files
        for f in rules.get("files", []):
            if f.casefold() in file_names_lower or any(f.casefold() in fn for fn in file_names_lower):
                findings.append({"type": "file", "finding": f"{f} file exists in repository"})
                evidence_records.append({"type": "file", "value": f})
                break

        # Check entry points
        for ep in rules.get("entry_points", []):
            if ep.casefold() in file_names_lower:
                findings.append({"type": "source_code", "finding": f"Application initialization/entry point found in {ep}"})
                evidence_records.append({"type": "source_code", "value": ep})
                break

        # Check documentation and topics
        for doc in rules.get("docs", []):
            if doc in topics:
                findings.append({"type": "topic", "finding": f"Topic '{doc}' tagged on repository"})
                break
            elif doc in description_text:
                findings.append({"type": "documentation", "finding": f"Description references {tech}"})
                break
            elif doc in readme_text[:2000]:
                findings.append({"type": "documentation", "finding": f"README documentation references {tech}"})
                break

        if findings:
            if tech not in technologies_detected:
                technologies_detected.append(tech)
            confidence = min(0.99, 0.85 + 0.04 * len(findings))
            skill_evidence_items.append({
                "skill": tech,
                "evidence_source": "github",
                "repository": name,
                "evidence": findings,
                "verified": True,
                "confidence": round(confidence, 2),
            })

    # Code quality hygiene score
    has_readme = bool(readme_obj)
    has_license = bool(repo.get("license"))
    quality_points = sum((
        30 if has_readme else 0,
        25 if has_tests else 0,
        15 if has_license else 0,
        15 if repo.get("description") else 0,
        15 if has_docker or has_workflows else 0,
    ))

    repo_evidence = {
        "candidate_id": None,
        "repository_name": name,
        "name": name,
        "full_name": repo.get("full_name"),
        "repository_url": repo.get("html_url"),
        "url": repo.get("html_url"),
        "description": repo.get("description") or "",
        "topics": repo.get("topics") or [],
        "primary_language": repo.get("language"),
        "languages": list(languages.keys()) if isinstance(languages, dict) else [],
        "languages_breakdown": languages or {},
        "technologies_detected": technologies_detected,
        "evidence": evidence_records,
        "stars": int(repo.get("stargazers_count") or 0),
        "forks": int(repo.get("forks_count") or 0),
        "fork": bool(repo.get("fork")),
        "archived": bool(repo.get("archived")),
        "default_branch": repo.get("default_branch") or "main",
        "pushed_at": repo.get("pushed_at"),
        "updated_at": repo.get("updated_at"),
        "created_at": repo.get("created_at"),
        "repository_metadata": {
            "created_at": repo.get("created_at"),
            "updated_at": repo.get("updated_at"),
            "pushed_at": repo.get("pushed_at"),
            "stars": int(repo.get("stargazers_count") or 0),
            "forks": int(repo.get("forks_count") or 0),
            "topics": repo.get("topics") or [],
            "default_branch": repo.get("default_branch") or "main",
        },
        "verification_status": "verified",
        "readme_evidence": {"checked": not limited_evidence, "present": has_readme, "url": (readme_obj or {}).get("html_url")},
        "testing_evidence": {"checked": not limited_evidence, "present": has_tests, "markers": [f for f in file_names if "test" in f.lower() or "spec" in f.lower()]},
        "deployment_evidence": {"docker": has_docker, "ci_cd": has_workflows},
        "code_quality": {
            "score": quality_points,
            "result": "strong" if quality_points >= 70 else "moderate" if quality_points >= 40 else "limited",
        },
    }

    return repo_evidence, skill_evidence_items


def verify_github_profile(value: str):
    """Retrieve full GitHub public profile and deep repository facts from the GitHub API."""
    username = github_username(value)
    profile, headers = _request(f"/users/{quote(username)}")
    repos, _ = _request(f"/users/{quote(username)}/repos?type=owner&sort=pushed&direction=desc&per_page=30")
    owned = [repo for repo in repos if not repo.get("fork") and not repo.get("archived")]
    authenticated = bool((os.getenv("GITHUB_TOKEN", "") or os.getenv("GH_TOKEN", "")).strip())
    # Deep inspection makes several API calls per repository. Keep anonymous
    # verification comfortably inside GitHub's small unauthenticated allowance.
    repository_limit = 6 if authenticated else 2
    ranked = sorted(
        owned,
        key=lambda repo: (repo.get("pushed_at") or "", repo.get("stargazers_count") or 0),
        reverse=True,
    )[:repository_limit]

    all_repo_evidence = []
    all_skill_evidence = []

    for repo in ranked:
        repo_data, skills = _inspect_repo(username, repo)
        all_repo_evidence.append(repo_data)
        all_skill_evidence.extend(skills)

    # Consolidate skill evidence by skill name (merging evidence across repositories)
    grouped_skills = {}
    for item in all_skill_evidence:
        skill_name = item["skill"]
        if skill_name not in grouped_skills:
            grouped_skills[skill_name] = {
                "skill": skill_name,
                "evidence_source": "github",
                "repository": item["repository"],
                "repositories": [item["repository"]],
                "evidence": list(item["evidence"]),
                "verified": True,
                "confidence": item["confidence"],
            }
        else:
            current = grouped_skills[skill_name]
            if item["repository"] not in current["repositories"]:
                current["repositories"].append(item["repository"])
            for finding in item["evidence"]:
                if finding not in current["evidence"]:
                    current["evidence"].append(finding)
            current["confidence"] = min(0.99, round(current["confidence"] + 0.02, 2))

    consolidated_skills = list(grouped_skills.values())

    language_bytes = Counter()
    for repo in all_repo_evidence:
        language_bytes.update(repo.get("languages_breakdown", {}))
    total_bytes = sum(language_bytes.values()) or 1
    languages = [{"name": name, "bytes": count, "percentage": round(count / total_bytes * 100, 1)} for name, count in language_bytes.most_common()]

    quality_score = round(sum(repo["code_quality"]["score"] for repo in all_repo_evidence) / len(all_repo_evidence), 1) if all_repo_evidence else 0
    tested_count = sum(bool(repo["testing_evidence"]["present"]) for repo in all_repo_evidence)
    docker_count = sum(bool(repo["deployment_evidence"]["docker"]) for repo in all_repo_evidence)
    workflow_count = sum(bool(repo["deployment_evidence"]["ci_cd"]) for repo in all_repo_evidence)
    verified_at = utcnow().isoformat()

    return {
        "github_url": profile.get("html_url"),
        "username": profile.get("login"),
        "source": "github_api",
        "verification_status": "verified",
        "verified_at": verified_at,
        "github_account_id": profile.get("id"),
        "profile": {
            "name": profile.get("name"),
            "bio": profile.get("bio"),
            "company": profile.get("company"),
            "location": profile.get("location"),
            "avatar_url": profile.get("avatar_url"),
            "public_repos": profile.get("public_repos"),
            "followers": profile.get("followers"),
            "created_at": profile.get("created_at"),
            "updated_at": profile.get("updated_at"),
        },
        "repositories": all_repo_evidence,
        "detected_skills": list(grouped_skills.keys()),
        "skill_evidence": consolidated_skills,
        "analysis": {
            "repository_count": len(owned),
            "selected_repository_count": len(all_repo_evidence),
            "selected_repositories": all_repo_evidence,
            "main_languages": languages,
            "readme_repository_count": sum(repo["readme_evidence"]["present"] is True for repo in all_repo_evidence),
            "tested_repository_count": tested_count,
            "dockerized_repository_count": docker_count,
            "ci_cd_repository_count": workflow_count,
            "code_quality_score": quality_score,
            "code_quality_result": "strong" if quality_score >= 70 else "moderate" if quality_score >= 40 else "limited",
        },
        "api_rate_limit_remaining": int(headers.get("X-RateLimit-Remaining", 0) or 0),
        "api_status": "success",
    }


def compute_cv_github_consistency(cv_skills: list[str], github_detected_skills: list[str]) -> dict:
    """Compare candidate CV claims against verified GitHub evidence."""
    github_keys = {normalize_skill(s): s for s in github_detected_skills if normalize_skill(s)}
    confirmed = []
    unverified = []
    seen = set()

    for cv_skill in cv_skills:
        clean = str(cv_skill or "").strip()
        key = normalize_skill(clean)
        if not key or key in seen:
            continue
        seen.add(key)
        matches_github = key in github_keys or any(
            min(len(key), len(g_key)) >= 3 and (key in g_key or g_key in key)
            for g_key in github_keys
        )
        if matches_github:
            confirmed.append(clean)
        else:
            unverified.append(clean)

    # Level of consistency
    total = len(confirmed) + len(unverified)
    ratio = (len(confirmed) / total) if total else 0.0
    if ratio >= 0.6 or len(confirmed) >= 4:
        level = "strong"
    elif ratio >= 0.3 or len(confirmed) >= 2:
        level = "moderate"
    elif len(confirmed) > 0:
        level = "partial"
    else:
        level = "not_verified_from_github"

    return {
        "confirmed_skills": confirmed,
        "unverified_skills": unverified,
        "contradictions": [],
        "consistency_level": level,
    }


def local_gemini_github_analysis(raw_github_data: dict, cv_skills: list[str], job: dict = None) -> dict:
    """Rule-based fallback if Gemini API is offline."""
    detected = raw_github_data.get("detected_skills", [])
    analysis = raw_github_data.get("analysis", {})
    repos = raw_github_data.get("repositories", [])
    tested_count = analysis.get("tested_repository_count", 0)
    docker_count = analysis.get("dockerized_repository_count", 0)
    quality_score = float(analysis.get("code_quality_score", 0))

    strengths = []
    weaknesses = []

    if detected:
        strengths.append(f"Strong evidence across {len(detected)} technologies: {', '.join(detected[:5])}")
    if docker_count > 0:
        strengths.append(f"{docker_count} repository with containerized Docker / deployment configuration")
    if quality_score >= 60:
        strengths.append("High repository documentation and hygiene standards")

    if tested_count == 0:
        weaknesses.append("Limited automated unit/integration test suites detected")
    if not docker_count:
        weaknesses.append("No containerization/Docker configuration found in sampled repositories")

    # Match percentage
    job_skills = [s.strip().casefold() for s in str((job or {}).get("skills", "")).split(",") if s.strip()]
    relevant_repos = []
    if job_skills:
        matched_job = [s for s in job_skills if any(normalize_skill(d) in s or s in normalize_skill(d) for d in detected)]
        match_percentage = round(min(100.0, (len(matched_job) / len(job_skills) * 60) + (quality_score * 0.4)), 1)
        for repo in repos[:3]:
            techs = repo.get("technologies_detected", [])
            overlap = [t for t in techs if any(normalize_skill(t) in s or s in normalize_skill(t) for s in job_skills)]
            if overlap:
                relevant_repos.append({
                    "repository": repo.get("name"),
                    "relevance": "high" if len(overlap) >= 2 else "medium",
                    "reason": f"Uses relevant technologies: {', '.join(overlap)}",
                })
    else:
        match_percentage = round(min(100.0, 50.0 + (quality_score * 0.5)), 1)
        for repo in repos[:2]:
            relevant_repos.append({
                "repository": repo.get("name"),
                "relevance": "medium",
                "reason": f"Demonstrates {', '.join(repo.get('technologies_detected', [])[:3])}",
            })

    return {
        "match_percentage": match_percentage,
        "strengths": strengths or ["Active public GitHub profile with verifiable repositories"],
        "weaknesses": weaknesses or ["Continue adding comprehensive test coverage"],
        "job_relevant_repositories": relevant_repos,
        "confidence": 0.92,
    }


async def analyze_github_with_gemini(raw_github_data: dict, cv_skills: list[str], job: dict = None, api_key: str = "", model_name: str = "gemini-3.5-flash-lite") -> dict:
    """Send normalized GitHub evidence to Gemini for technical analysis."""
    if not api_key:
        return local_gemini_github_analysis(raw_github_data, cv_skills, job)

    repos_summary = []
    for r in raw_github_data.get("repositories", [])[:6]:
        repos_summary.append({
            "name": r.get("name"),
            "url": r.get("repository_url"),
            "description": r.get("description"),
            "languages": r.get("languages"),
            "technologies": r.get("technologies_detected"),
            "has_tests": r.get("testing_evidence", {}).get("present"),
            "has_docker": r.get("deployment_evidence", {}).get("docker"),
            "has_ci_cd": r.get("deployment_evidence", {}).get("ci_cd"),
            "stars": r.get("stars"),
            "pushed_at": r.get("pushed_at"),
        })

    prompt = f"""
You are an expert technical evaluator and hiring system analyzing verified GitHub evidence collected by backend API calls.
Do NOT browse or invent GitHub data. Rely ONLY on the verified data provided below.

JOB REQUIREMENT (Optional Context):
{json.dumps(job or {}, default=str)}

CANDIDATE CV TECHNICAL CLAIMS:
{json.dumps(cv_skills, default=str)}

VERIFIED GITHUB PROFILE & REPOSITORIES:
Username: {raw_github_data.get("username")}
Bio: {raw_github_data.get("profile", {}).get("bio")}
Public Repositories: {raw_github_data.get("profile", {}).get("public_repos")}
Detected Technologies: {json.dumps(raw_github_data.get("detected_skills", []))}
Repositories: {json.dumps(repos_summary, default=str)}

Evaluate:
1. Technical relevance and alignment with professional standards (and Job requirements if present).
2. Project complexity and code/project hygiene.
3. Evidence strength for key claimed skills.
4. Testing evidence and deployment/containerization evidence.
5. CV-to-GitHub consistency.

Return ONLY a valid JSON object matching this exact schema:
{{
    "match_percentage": 85.0,
    "strengths": ["Strong FastAPI backend evidence", "Multiple Dockerized projects", "Good AI/ML repository relevance"],
    "weaknesses": ["Limited automated test evidence"],
    "job_relevant_repositories": [
        {{"repository": "repository-name", "relevance": "high|medium|low", "reason": "Specific technical alignment reason."}}
    ],
    "confidence": 0.93
}}
"""
    try:
        result = await generate_gemini_json(api_key, model_name, prompt)
        if "github_analysis" in result and isinstance(result["github_analysis"], dict):
            result = result["github_analysis"]
        return {
            "match_percentage": float(result.get("match_percentage", 80.0)),
            "strengths": [str(s) for s in result.get("strengths", [])],
            "weaknesses": [str(w) for w in result.get("weaknesses", [])],
            "job_relevant_repositories": [
                {
                    "repository": str(item.get("repository", "")),
                    "relevance": str(item.get("relevance", "medium")),
                    "reason": str(item.get("reason", "")),
                }
                for item in result.get("job_relevant_repositories", [])
                if isinstance(item, dict)
            ],
            "confidence": float(result.get("confidence", 0.92)),
        }
    except Exception:
        return local_gemini_github_analysis(raw_github_data, cv_skills, job)


def compare_github_snapshots(prev_snap: dict, curr_snap: dict) -> dict:
    """Compare two historical GitHub evidence snapshots for progress tracking."""
    if not prev_snap or not curr_snap:
        return {"previous_snapshot": None, "current_snapshot": (curr_snap or {}).get("scanned_at"), "changes": {"new_repositories": [], "new_skills_detected": [], "updated_repositories": [], "new_evidence": []}}

    prev_repos = {r.get("repository_name") or r.get("name"): r for r in prev_snap.get("repositories", [])}
    curr_repos = {r.get("repository_name") or r.get("name"): r for r in curr_snap.get("repositories", [])}

    prev_skills = set(prev_snap.get("detected_skills", []))
    curr_skills = set(curr_snap.get("detected_skills", []))

    new_repos = [name for name in curr_repos if name not in prev_repos]
    new_skills = [skill for skill in curr_skills if skill not in prev_skills]

    updated_repos = []
    new_evidence = []

    for name, curr_r in curr_repos.items():
        if name in prev_repos:
            prev_r = prev_repos[name]
            # Check if pushed_at changed
            if curr_r.get("pushed_at") != prev_r.get("pushed_at"):
                updated_repos.append(name)
            # Check if tests were added
            curr_tests = curr_r.get("testing_evidence", {}).get("present")
            prev_tests = prev_r.get("testing_evidence", {}).get("present")
            if curr_tests and not prev_tests:
                new_evidence.append(f"Added unit/automated tests to '{name}'")
            # Check if Docker was added
            curr_docker = curr_r.get("deployment_evidence", {}).get("docker")
            prev_docker = prev_r.get("deployment_evidence", {}).get("docker")
            if curr_docker and not prev_docker:
                new_evidence.append(f"Added Dockerfile / containerization to '{name}'")
            # Check if CI/CD was added
            curr_ci = curr_r.get("deployment_evidence", {}).get("ci_cd")
            prev_ci = prev_r.get("deployment_evidence", {}).get("ci_cd")
            if curr_ci and not prev_ci:
                new_evidence.append(f"Added CI/CD workflows to '{name}'")

    for skill in new_skills:
        new_evidence.append(f"Detected new verified skill: {skill}")

    return {
        "previous_snapshot": prev_snap.get("scanned_at"),
        "current_snapshot": curr_snap.get("scanned_at"),
        "changes": {
            "new_repositories": new_repos,
            "new_skills_detected": new_skills,
            "updated_repositories": updated_repos,
            "new_evidence": new_evidence,
        },
    }


def github_skill_records(candidate_id: str, snapshot: dict) -> list[dict]:
    """Create persistent candidate_skills database records from a verified snapshot."""
    records = []
    stamp = utcnow()
    for skill_item in snapshot.get("skill_evidence", []):
        name = skill_item["skill"]
        findings = [f.get("finding") for f in skill_item.get("evidence", []) if isinstance(f, dict)]
        records.append({
            "id": identifier(),
            "candidate_id": candidate_id,
            "skill": name,
            "normalized_skill": normalize_skill(name),
            "kind": "technical",
            "category": "github_verified",
            "source": "github_api",
            "sources": ["github_api"],
            "evidence": findings or [f"GitHub API verified in repository '{skill_item.get('repository')}'"],
            "repository": skill_item.get("repository"),
            "confidence": skill_item.get("confidence", 0.95),
            "verified_by_recruiter": False,
            "verified_at": snapshot.get("scanned_at"),
            "updated_at": stamp,
            "created_at": stamp,
        })
    return records
