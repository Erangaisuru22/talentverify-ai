"""Small Gemini REST client used instead of a heavyweight/deprecated SDK."""

import json
import os
import shutil
import ssl
import subprocess
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

_USE_CURL = os.name == "nt"


class GeminiRestError(Exception):
    pass


def _response_text(response):
    candidates = response.get("candidates") or []
    if not candidates:
        reason = (response.get("promptFeedback") or {}).get("blockReason") or "no candidate returned"
        raise GeminiRestError(f"Gemini returned no result: {reason}")
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text = "".join(str(part.get("text") or "") for part in parts).strip()
    if not text:
        raise GeminiRestError(f"Gemini returned an empty result ({candidates[0].get('finishReason', 'unknown')}).")
    return text


def _curl_post(url, api_key, payload, timeout):
    executable = shutil.which("curl.exe") or shutil.which("curl")
    if not executable:
        raise GeminiRestError("Secure TLS fallback is unavailable.")
    config_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".curl.conf", delete=False, encoding="utf-8") as config:
            config_path = config.name
            config.write(f'url = "{url}"\nrequest = "POST"\nsilent\nshow-error\nfail-with-body\n')
            config.write(f'max-time = {int(timeout)}\nheader = "Content-Type: application/json"\n')
            config.write(f'header = "x-goog-api-key: {api_key}"\n')
        result = subprocess.run([executable, "--config", config_path, "--data-binary", "@-", "--write-out", "\n%{http_code}"],
                                input=payload, capture_output=True, text=True, timeout=timeout + 5, check=False)
        body, _, status_text = result.stdout.rpartition("\n")
        status = int(status_text) if status_text.isdigit() else 0
        if result.returncode or not 200 <= status < 300:
            try: message = (json.loads(body).get("error") or {}).get("message")
            except json.JSONDecodeError: message = None
            raise GeminiRestError(message or f"Gemini REST request failed (HTTP {status or 'unknown'}).")
        return json.loads(body)
    except subprocess.TimeoutExpired as exc:
        raise GeminiRestError("Gemini REST request timed out.") from exc
    finally:
        if config_path:
            try: os.unlink(config_path)
            except OSError: pass


def generate_json(api_key, model, prompt, max_output_tokens=8192, timeout=45):
    global _USE_CURL
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model, safe='')}:generateContent"
    request_body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0, "maxOutputTokens": max_output_tokens,
                                           "responseMimeType": "application/json"}}
    payload = json.dumps(request_body, ensure_ascii=False)
    if _USE_CURL:
        response = _curl_post(url, api_key, payload, timeout)
    else:
        try:
            request = Request(url, data=payload.encode("utf-8"), method="POST",
                              headers={"Content-Type": "application/json", "x-goog-api-key": api_key})
            with urlopen(request, timeout=timeout) as raw:
                response = json.loads(raw.read().decode("utf-8"))
        except HTTPError as exc:
            try: message = (json.loads(exc.read().decode("utf-8")).get("error") or {}).get("message")
            except Exception: message = None
            raise GeminiRestError(message or f"Gemini REST returned HTTP {exc.code}.") from exc
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), ssl.SSLCertVerificationError):
                _USE_CURL = True
                response = _curl_post(url, api_key, payload, timeout)
            else:
                raise GeminiRestError(f"Gemini connection failed: {getattr(exc, 'reason', exc)}") from exc
    text = _response_text(response).replace("```json", "").replace("```", "").strip()
    try: return json.loads(text)
    except json.JSONDecodeError as exc: raise GeminiRestError("Gemini returned incomplete JSON. Please retry.") from exc
