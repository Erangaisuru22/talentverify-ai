"""Consent-based LinkedIn verification using the official Verified on LinkedIn APIs."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class LinkedInVerificationError(Exception):
    pass


def configuration():
    tier = os.getenv("LINKEDIN_VERIFIED_TIER", "development").strip().casefold()
    return {
        "client_id": os.getenv("LINKEDIN_CLIENT_ID", "").strip(),
        "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET", "").strip(),
        "redirect_uri": os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/api/linkedin/oauth/callback").strip(),
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/"),
        "tier": tier if tier in {"development", "lite", "plus"} else "development",
        "version": os.getenv("LINKEDIN_API_VERSION", "202607").strip(),
    }


def scopes(tier):
    if tier == "plus":
        return ["r_profile_basicinfo", "r_verify_details", "r_primary_current_experience", "r_most_recent_education"]
    return ["r_profile_basicinfo", "r_verify"]


def authorization_url(state):
    config = configuration()
    if not config["client_id"] or not config["client_secret"]:
        raise LinkedInVerificationError("LinkedIn API is not configured. Add LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET.")
    query = urlencode({"response_type": "code", "client_id": config["client_id"],
                       "redirect_uri": config["redirect_uri"], "scope": " ".join(scopes(config["tier"])), "state": state})
    return f"https://www.linkedin.com/oauth/v2/authorization?{query}"


def _request(url, *, data=None, access_token=None, version=None):
    headers = {"Accept": "application/json", "User-Agent": "TalentVerify/2.0"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    if version:
        headers["LinkedIn-Version"] = version
        headers["X-Restli-Protocol-Version"] = "2.0.0"
    encoded = urlencode(data).encode() if data else None
    if encoded: headers["Content-Type"] = "application/x-www-form-urlencoded"
    try:
        with urlopen(Request(url, data=encoded, headers=headers), timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise LinkedInVerificationError(f"LinkedIn API rejected the request ({exc.code}): {detail}") from exc
    except (URLError, TimeoutError, ValueError) as exc:
        raise LinkedInVerificationError("Could not reach the LinkedIn API.") from exc


def exchange_and_collect(code):
    config = configuration()
    token = _request("https://www.linkedin.com/oauth/v2/accessToken", data={
        "grant_type": "authorization_code", "code": code, "client_id": config["client_id"],
        "client_secret": config["client_secret"], "redirect_uri": config["redirect_uri"],
    }).get("access_token")
    if not token:
        raise LinkedInVerificationError("LinkedIn did not return an access token.")
    identity = _request("https://api.linkedin.com/rest/identityMe", access_token=token, version=config["version"])
    report = _request("https://api.linkedin.com/rest/verificationReport", access_token=token, version=config["version"])
    return identity, report


def evidence_summary(identity, report, verified_at, tier):
    categories = [str(item).upper() for item in report.get("verifications", []) if item]
    basic = identity.get("basicInfo") or {}
    education = identity.get("mostRecentEducation")
    experience = identity.get("primaryCurrentPosition")
    return {
        "verification_status": "verified" if categories else "connected_unverified",
        "verified_at": verified_at,
        "linkedin_member_id": identity.get("id") or report.get("id"),
        "profile_url": basic.get("profileUrl"),
        "verified_categories": categories,
        "identity_verified": "IDENTITY" in categories,
        "workplace_verified": "WORKPLACE" in categories,
        "education": {"status": "available" if education else "not_returned", "evidence": education},
        "experience": {"status": "available" if experience else "not_returned", "evidence": experience},
        "skills": {"status": "unsupported_by_linkedin_api", "evidence": []},
        "soft_skills": {"status": "unsupported_by_linkedin_api", "evidence": []},
        "certifications": {"status": "unsupported_by_linkedin_api", "evidence": []},
        "tier": tier,
        "source": "linkedin_verified_api",
    }
