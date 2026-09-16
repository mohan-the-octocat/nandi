"""Google Cloud Model Armor REST Client with ADC Auth & Retry Logic."""

import dataclasses
import datetime
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple

# ------------------------------------------------------------------------------
# Failure taxonomy
#
# These categories distinguish "the control could not run" from "the control ran
# and rejected the prompt". Both still fail closed, but they are different events
# and must not be conflated in the developer message or the regulatory audit log.
# ------------------------------------------------------------------------------
FAILURE_AUTH_MISSING = "AUTH_MISSING"
FAILURE_AUTH_STALE = "AUTH_STALE"
FAILURE_AUTH_REJECTED = "AUTH_REJECTED"
FAILURE_PERMISSION_DENIED = "PERMISSION_DENIED"
FAILURE_TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
FAILURE_UNREACHABLE = "UNREACHABLE"
FAILURE_API_ERROR = "API_ERROR"

REMEDIATION_BY_CATEGORY: Dict[str, str] = {
    FAILURE_AUTH_MISSING: (
        "No Google Cloud credential could be found. Ensure your credential refresh "
        "agent is running, or run 'gcloud auth application-default login'."
    ),
    FAILURE_AUTH_STALE: (
        "Your local Google Cloud credential has expired. Reconnect to the corporate "
        "network/VPN so the credential refresh agent can renew it, or run "
        "'gcloud auth application-default login'."
    ),
    FAILURE_AUTH_REJECTED: (
        "Google Cloud rejected the local credential (HTTP 401) even after refresh. "
        "Re-authenticate via your corporate SSO, or run "
        "'gcloud auth application-default login'."
    ),
    FAILURE_PERMISSION_DENIED: (
        "The authenticated identity lacks Model Armor permissions on this project. "
        "Ask your GCP administrator for roles/modelarmor.user."
    ),
    FAILURE_TEMPLATE_NOT_FOUND: (
        "The configured Model Armor template does not exist. Verify template_id, "
        "location, and project_id in config/config.yaml."
    ),
    FAILURE_UNREACHABLE: (
        "Model Armor could not be reached. Check network connectivity, VPN, and "
        "proxy settings, then retry."
    ),
    FAILURE_API_ERROR: (
        "Model Armor returned an unexpected error. Retry; if it persists, contact "
        "your platform team."
    ),
}

# A bare access token file carries no expiry, so its age is bounded by the standard
# Google OAuth2 access token lifetime. Anything older is presumed dead.
DEFAULT_TOKEN_FILE_MAX_AGE_SECONDS = 3600.0

# Treat a token as already expired this many seconds before its true expiry, so a
# token does not die mid-flight between acquisition and the API call.
DEFAULT_TOKEN_EXPIRY_MARGIN_SECONDS = 300.0


def _remediation_for(category: Optional[str]) -> str:
    return REMEDIATION_BY_CATEGORY.get(category or "", REMEDIATION_BY_CATEGORY[FAILURE_API_ERROR])


@dataclasses.dataclass
class ModelArmorRequest:
    """Request payload for Model Armor SanitizeUserPrompt API."""
    project_id: str
    location: str
    template_id: str
    user_prompt: str
    enable_multi_language: bool = True
    source_language: Optional[str] = None

    @property
    def template_resource_name(self) -> str:
        return f"projects/{self.project_id}/locations/{self.location}/templates/{self.template_id}"

    def to_api_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": self.template_resource_name,
            "user_prompt_data": {
                "text": self.user_prompt
            }
        }
        if self.enable_multi_language:
            payload["multi_language_detection_metadata"] = {
                "enable_multi_language_detection": True
            }
            if self.source_language:
                payload["multi_language_detection_metadata"]["source_language"] = self.source_language
        return payload


@dataclasses.dataclass
class ModelArmorResponse:
    """Response wrapper for Model Armor SanitizeUserPrompt API."""
    success: bool
    raw_response: Dict[str, Any]
    filter_match_state: str  # NO_MATCH_FOUND or MATCH_FOUND
    invocation_result: str   # SUCCESS, PARTIAL, FAILURE
    filter_results: Dict[str, Any]
    sanitized_text: Optional[str] = None
    error_message: Optional[str] = None
    status_code: int = 200
    latency_ms: float = 0.0
    # Set only when the prompt could NOT be adjudicated (auth, network, config).
    # None means Model Armor actually ran and returned a verdict.
    failure_category: Optional[str] = None
    remediation: Optional[str] = None

    @property
    def is_infrastructure_failure(self) -> bool:
        """True when the prompt was never evaluated, as opposed to being rejected."""
        return self.failure_category is not None



class ModelArmorClient:
    """Client for Google Cloud Model Armor API (modelarmor.googleapis.com)."""

    _auth_attempted: bool = False
    _cached_token: Optional[str] = None
    _cached_token_expiry: Optional[float] = None
    _auth_source: Optional[str] = None
    _auth_failure_reason: Optional[str] = None
    _auth_failure_category: Optional[str] = None

    def __init__(
        self,
        project_id: str = "your-gcp-project-id",
        location: str = "asia-south1",
        template_id: str = "Nandi-compliance-template",
        endpoint: Optional[str] = None,
        timeout_seconds: float = 5.0,
        retry_attempts: int = 2,
    ):
        # Resolve project_id: environment variable > config.yaml > parameter default
        env_pid = os.environ.get("MODEL_ARMOR_PROJECT_ID")
        if env_pid:
            self.project_id = env_pid
        else:
            cfg_pid = None
            try:
                cfg_file = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "config",
                    "config.yaml"
                )
                if os.path.exists(cfg_file):
                    import re
                    with open(cfg_file, "r", encoding="utf-8") as f:
                        m = re.search(r'project_id:\s*["\']([^"\']+)["\']', f.read())
                        if m:
                            cfg_pid = m.group(1)
            except Exception:
                pass
            self.project_id = cfg_pid or project_id
        self.location = os.environ.get("MODEL_ARMOR_LOCATION", location)
        self.template_id = os.environ.get("MODEL_ARMOR_TEMPLATE_ID", template_id)
        self.endpoint = endpoint or os.environ.get("MODEL_ARMOR_ENDPOINT")
        self.timeout_seconds = timeout_seconds
        self.retry_attempts = retry_attempts

    # --------------------------------------------------------------------------
    # Credential acquisition
    # --------------------------------------------------------------------------

    @staticmethod
    def _expiry_margin_seconds() -> float:
        try:
            return float(os.environ.get(
                "NANDI_TOKEN_EXPIRY_MARGIN_SECONDS", DEFAULT_TOKEN_EXPIRY_MARGIN_SECONDS))
        except (TypeError, ValueError):
            return DEFAULT_TOKEN_EXPIRY_MARGIN_SECONDS

    @staticmethod
    def _token_file_max_age_seconds() -> float:
        try:
            return float(os.environ.get(
                "NANDI_TOKEN_FILE_MAX_AGE_SECONDS", DEFAULT_TOKEN_FILE_MAX_AGE_SECONDS))
        except (TypeError, ValueError):
            return DEFAULT_TOKEN_FILE_MAX_AGE_SECONDS

    @classmethod
    def _is_live(cls, expiry_epoch: Optional[float]) -> bool:
        """True if a token with this expiry is still safe to use."""
        if expiry_epoch is None:
            return True  # Expiry unknown; the caller decides whether to trust it.
        return time.time() < (expiry_epoch - cls._expiry_margin_seconds())

    @staticmethod
    def _parse_expiry(value: Any) -> Optional[float]:
        """Coerces an expiry given as epoch seconds or ISO-8601 into epoch float."""
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return None
            try:
                return float(raw)
            except ValueError:
                pass
            try:
                parsed = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            return parsed.timestamp()
        return None

    def _read_token_file(self, token_file: str) -> Tuple[Optional[str], Optional[float], Optional[str]]:
        """Reads a credential file and returns (token, expiry_epoch, skip_reason).

        Two on-disk formats are supported:
          1. JSON envelope -- {"token": "ACCESS_TOKEN", "expiry": "2026-09-16T09:00:00Z"}.
             'access_token', 'expires_at', 'expireTime' and 'expires_in' are also
             accepted, so a refresh agent can publish an explicit lifetime.
          2. Bare token string -- carries no expiry, so its life is bounded by the
             file mtime plus the standard OAuth2 access token lifetime.

        A token that is missing, malformed or past expiry returns (None, None,
        reason). Returning a reason rather than the token is what allows the caller
        to fall through to the next credential source instead of presenting a dead
        token to the API.
        """
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
        except Exception as e:
            return None, None, f"credential file '{token_file}' is unreadable ({e})"

        if not content:
            return None, None, f"credential file '{token_file}' is empty"

        token: Optional[str] = None
        expiry: Optional[float] = None

        if content.startswith("{"):
            try:
                envelope = json.loads(content)
            except ValueError:
                return None, None, f"credential file '{token_file}' contains malformed JSON"
            if not isinstance(envelope, dict):
                return None, None, f"credential file '{token_file}' has an unexpected JSON payload"

            raw_token = envelope.get("token") or envelope.get("access_token")
            if raw_token:
                token = str(raw_token).strip()
            expiry = self._parse_expiry(
                envelope.get("expiry")
                or envelope.get("expires_at")
                or envelope.get("expireTime")
            )
            if expiry is None and envelope.get("expires_in") is not None:
                try:
                    expiry = os.path.getmtime(token_file) + float(envelope["expires_in"])
                except (OSError, TypeError, ValueError):
                    expiry = None
        else:
            token = content

        if not token:
            return None, None, f"credential file '{token_file}' contains no token"

        if expiry is None:
            try:
                expiry = os.path.getmtime(token_file) + self._token_file_max_age_seconds()
            except OSError:
                return None, None, f"age of credential file '{token_file}' could not be determined"

        if not self._is_live(expiry):
            expired_at = datetime.datetime.fromtimestamp(
                expiry, datetime.timezone.utc).isoformat()
            return None, None, f"credential file '{token_file}' expired at {expired_at}"

        return token, expiry, None

    @classmethod
    def _cache_token(cls, token: str, expiry: Optional[float], source: str) -> str:
        cls._cached_token = token
        cls._cached_token_expiry = expiry
        cls._auth_attempted = True
        cls._auth_source = source
        cls._auth_failure_reason = None
        cls._auth_failure_category = None
        return token

    @classmethod
    def reset_auth_cache(cls) -> None:
        """Clears the process-wide credential cache."""
        cls._auth_attempted = False
        cls._cached_token = None
        cls._cached_token_expiry = None
        cls._auth_source = None
        cls._auth_failure_reason = None
        cls._auth_failure_category = None

    @classmethod
    def auth_failure_category(cls) -> str:
        return cls._auth_failure_category or FAILURE_AUTH_MISSING

    @classmethod
    def auth_failure_detail(cls) -> Optional[str]:
        return cls._auth_failure_reason

    def _refresh_auth_token(self) -> Optional[str]:
        """Discards the cached credential and resolves a fresh one.

        Used when the API rejects the current token with HTTP 401, which is the
        only reliable signal that a cached or on-disk token has gone bad.
        """
        ModelArmorClient.reset_auth_cache()
        return self._get_auth_token()

    def _token_from_adc(self) -> Tuple[Optional[str], Optional[float], Optional[str]]:
        """Resolves a token from in-process Application Default Credentials.

        Returns (token, expiry_epoch, skip_reason). Kept as its own method so the
        ADC source can be exercised in isolation regardless of whether google-auth
        happens to be installed in the running interpreter.
        """
        try:
            import google.auth
            import google.auth.transport.requests
        except Exception as e:
            return None, None, f"google-auth unavailable ({e})"

        try:
            creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            creds.refresh(google.auth.transport.requests.Request())
        except Exception as e:
            return None, None, f"application default credentials unavailable ({e})"

        if not creds.token:
            return None, None, "application default credentials returned no token"

        expiry = None
        creds_expiry = getattr(creds, "expiry", None)
        if creds_expiry is not None:
            try:
                if creds_expiry.tzinfo is None:
                    creds_expiry = creds_expiry.replace(tzinfo=datetime.timezone.utc)
                expiry = creds_expiry.timestamp()
            except (AttributeError, TypeError, ValueError, OSError):
                expiry = None
        return creds.token, expiry, None

    def _token_from_gcloud(self) -> Tuple[Optional[str], Optional[float], Optional[str]]:
        """Resolves a token by shelling out to the gcloud CLI (~1.3s-2.5s on gLinux)."""
        reasons = []
        for cmd in (["gcloud", "auth", "print-access-token"],
                    ["gcloud", "auth", "application-default", "print-access-token"]):
            try:
                res = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=4.0,
                    check=False,
                )
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip(), None, None
                if res.stderr and res.stderr.strip():
                    reasons.append(f"'{' '.join(cmd)}' failed: {res.stderr.strip().splitlines()[0]}")
            except Exception as e:
                reasons.append(f"'{' '.join(cmd)}' failed ({e})")
        return None, None, "; ".join(reasons) if reasons else "gcloud produced no token"

    def _get_auth_token(self) -> Optional[str]:
        """Resolves a live GCP OAuth2 access token.

        Sources are tried in priority order: explicit environment variable, local
        credential file, in-process ADC, then the gcloud CLI.

        A source that yields a stale or unusable credential is SKIPPED, not
        returned. This matters on a laptop resuming from a long offline period: a
        dead token left on disk by a refresh agent must not mask an otherwise
        working credential further down the chain.
        """
        if os.environ.get("MODEL_ARMOR_NO_AUTH") == "1":
            return None

        cls = ModelArmorClient

        if cls._auth_attempted and cls._cached_token:
            if cls._is_live(cls._cached_token_expiry):
                return cls._cached_token
            # Cached token has since expired; drop it and resolve again.
            cls._cached_token = None
            cls._cached_token_expiry = None

        skipped: list = []

        # 1. Explicit environment variable (operator-injected, trusted as supplied)
        env_token = os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN") or os.environ.get("GCP_ACCESS_TOKEN")
        if env_token and env_token.strip():
            return cls._cache_token(env_token.strip(), None, "environment")

        # 2. Credential file published by a local refresh agent
        token_file = os.environ.get("GCP_ACCESS_TOKEN_FILE") or os.path.expanduser(
            "~/.config/gcloud/access_token")
        if os.path.exists(token_file):
            token, expiry, skip_reason = self._read_token_file(token_file)
            if token:
                return cls._cache_token(token, expiry, "token_file")
            if skip_reason:
                skipped.append(skip_reason)

        # 3. In-process Application Default Credentials (fast, no subprocess)
        token, expiry, skip_reason = self._token_from_adc()
        if token:
            return cls._cache_token(token, expiry, "adc")
        if skip_reason:
            skipped.append(skip_reason)

        # 4. Fall back to the gcloud CLI
        token, expiry, skip_reason = self._token_from_gcloud()
        if token:
            return cls._cache_token(token, expiry, "gcloud")
        if skip_reason:
            skipped.append(skip_reason)

        cls._auth_attempted = True
        cls._cached_token = None
        cls._cached_token_expiry = None
        cls._auth_source = None
        cls._auth_failure_reason = "; ".join(skipped) if skipped else None
        cls._auth_failure_category = (
            FAILURE_AUTH_STALE
            if any("expired" in reason for reason in skipped)
            else FAILURE_AUTH_MISSING
        )
        return None


    # --------------------------------------------------------------------------
    # Authenticated transport
    # --------------------------------------------------------------------------

    def _authenticated_request(
        self,
        url: str,
        payload_bytes: Optional[bytes],
        method: str,
        project_id: str,
    ) -> Tuple[Optional[Dict[str, Any]], int, Optional[str], Optional[str]]:
        """Performs an authenticated JSON call, refreshing once on HTTP 401.

        Returns (data, status_code, failure_category, error_message). On success
        failure_category is None.

        A 401 means the token is bad, so retrying with the same token is pointless.
        The credential is refreshed once and the call retried; if it still fails the
        loop exits immediately rather than burning the remaining attempts.
        """
        token = self._get_auth_token()
        if not token:
            detail = ModelArmorClient.auth_failure_detail()
            category = ModelArmorClient.auth_failure_category()
            message = "Unable to obtain a valid GCP OAuth2 access token."
            if detail:
                message = f"{message} Tried: {detail}."
            return None, 401, category, message

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token}",
            "X-Goog-User-Project": project_id,
        }

        refreshed = False
        last_error: Optional[str] = None
        last_status = 0
        last_category = FAILURE_UNREACHABLE
        attempt = 0

        while attempt <= self.retry_attempts:
            try:
                http_req = urllib.request.Request(
                    url, data=payload_bytes, headers=headers, method=method)
                with urllib.request.urlopen(http_req, timeout=self.timeout_seconds) as resp:
                    body = resp.read().decode("utf-8")
                    return json.loads(body), getattr(resp, "status", 200), None, None
            except urllib.error.HTTPError as e:
                err_content = e.read().decode("utf-8", errors="ignore")
                last_error = f"HTTP {e.code}: {e.reason} - {err_content}"
                last_status = e.code

                if e.code == 401:
                    if not refreshed:
                        refreshed = True
                        new_token = self._refresh_auth_token()
                        if new_token and new_token != token:
                            token = new_token
                            headers["Authorization"] = f"Bearer {token}"
                            continue
                    last_category = FAILURE_AUTH_REJECTED
                    break
                if e.code == 403:
                    last_category = FAILURE_PERMISSION_DENIED
                    break
                if e.code == 404:
                    last_category = FAILURE_TEMPLATE_NOT_FOUND
                    break
                if e.code == 400:
                    last_category = FAILURE_API_ERROR
                    break
                last_category = FAILURE_API_ERROR
            except Exception as e:
                last_error = str(e)
                last_category = FAILURE_UNREACHABLE

            attempt += 1
            if attempt <= self.retry_attempts:
                time.sleep(0.1 * (2 ** (attempt - 1)))

        return None, last_status, last_category, last_error


    def _resolve_endpoint(self, loc: str) -> str:
        if self.endpoint:
            return self.endpoint
        if loc == "global":
            return "modelarmor.googleapis.com"
        return f"modelarmor.{loc}.rep.googleapis.com"

    def sanitize_user_prompt(
        self,
        prompt: str,
        template_id: Optional[str] = None,
        location: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> ModelArmorResponse:
        """Invokes the Model Armor SanitizeUserPrompt API.

        On failure the prompt is blocked (fail-closed), but the response carries a
        failure_category and remediation so callers can tell "the control could not
        run" apart from "the control rejected this prompt".
        """
        start_time = time.perf_counter()
        proj = project_id or self.project_id
        loc = location or self.location
        tmpl = template_id or self.template_id

        req = ModelArmorRequest(
            project_id=proj,
            location=loc,
            template_id=tmpl,
            user_prompt=prompt,
        )

        url = f"https://{self._resolve_endpoint(loc)}/v1/{req.template_resource_name}:sanitizeUserPrompt"
        payload_bytes = json.dumps(req.to_api_payload()).encode("utf-8")

        data, status_code, failure_category, error_message = self._authenticated_request(
            url=url,
            payload_bytes=payload_bytes,
            method="POST",
            project_id=proj,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        if failure_category is None and data is not None:
            s_result = data.get("sanitizationResult") or data.get("sanitization_result", {})
            return ModelArmorResponse(
                success=True,
                raw_response=data,
                filter_match_state=(
                    s_result.get("filterMatchState")
                    or s_result.get("filter_match_state", "NO_MATCH_FOUND")
                ),
                invocation_result=(
                    s_result.get("invocationResult")
                    or s_result.get("invocation_result", "SUCCESS")
                ),
                filter_results=(
                    s_result.get("filterResults")
                    or s_result.get("filter_results", {})
                ),
                sanitized_text=prompt,
                status_code=status_code,
                latency_ms=elapsed_ms,
            )

        # Fail-closed: the prompt was never adjudicated, so it does not propagate.
        remediation = _remediation_for(failure_category)
        return ModelArmorResponse(
            success=False,
            raw_response={},
            filter_match_state="NO_MATCH_FOUND",
            invocation_result="FAILURE",
            filter_results={},
            error_message=f"{error_message} Prompt blocked under fail-closed security policy.",
            status_code=status_code,
            latency_ms=elapsed_ms,
            failure_category=failure_category or FAILURE_API_ERROR,
            remediation=remediation,
        )


    def get_template(
        self,
        template_id: Optional[str] = None,
        location: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetches Model Armor template metadata from the GCP Regional Endpoint.

        Args:
            template_id: Optional template ID override (defaults to self.template_id).
            location: Optional location override (defaults to self.location).
            project_id: Optional project ID override (defaults to self.project_id).

        Returns:
            Dict containing:
                - success (bool): True if template exists and was successfully retrieved.
                - template (dict): Template definition and filter configurations from GCP.
                - status_code (int): HTTP status code (200, 404, 403, etc.) or 0 if connection error.
                - error_message (Optional[str]): Error description if call failed.
                - resource_name (str): Full GCP resource name of the template.
        """
        proj = project_id or self.project_id
        loc = location or self.location
        tmpl = template_id or self.template_id

        template_resource_name = f"projects/{proj}/locations/{loc}/templates/{tmpl}"
        url = f"https://{self._resolve_endpoint(loc)}/v1/{template_resource_name}"

        data, status_code, failure_category, error_message = self._authenticated_request(
            url=url,
            payload_bytes=None,
            method="GET",
            project_id=proj,
        )

        if failure_category is None and data is not None:
            return {
                "success": True,
                "template": data,
                "status_code": status_code,
                "error_message": None,
                "resource_name": template_resource_name,
                "failure_category": None,
                "remediation": None,
            }

        if failure_category in (FAILURE_AUTH_MISSING, FAILURE_AUTH_STALE, FAILURE_AUTH_REJECTED):
            error_message = f"Authentication failed: {error_message}"

        return {
            "success": False,
            "template": {},
            "status_code": status_code,
            "error_message": error_message,
            "resource_name": template_resource_name,
            "failure_category": failure_category,
            "remediation": _remediation_for(failure_category),
        }


    def check_iam_permissions(
        self,
        project_id: Optional[str] = None,
        required_permissions: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Validates whether the authenticated identity has requisite Model Armor IAM permissions.

        Evaluates effective permissions across direct user grants, Google Groups memberships,
        and resource hierarchy inheritance using Cloud Resource Manager testIamPermissions.

        Default required permissions:
          - modelarmor.templates.useToSanitizeUserPrompt (from roles/modelarmor.user, admin, editor, owner)
          - modelarmor.templates.get (from roles/modelarmor.viewer, admin, editor, owner)
        """
        proj = project_id or self.project_id
        req_perms = required_permissions or [
            "modelarmor.templates.useToSanitizeUserPrompt",
            "modelarmor.templates.get",
        ]

        auth_token = self._get_auth_token()
        if not auth_token:
            return {
                "success": False,
                "project_id": proj,
                "status_code": 401,
                "granted_permissions": [],
                "missing_permissions": req_perms,
                "has_sanitize_permission": False,
                "has_view_permission": False,
                "error_message": "Authentication failed: Unable to obtain GCP OAuth2 access token for IAM validation.",
            }

        url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{proj}:testIamPermissions"
        payload = json.dumps({"permissions": req_perms}).encode("utf-8")
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {auth_token}",
        }

        last_error = None
        for attempt in range(self.retry_attempts + 1):
            try:
                http_req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(http_req, timeout=self.timeout_seconds) as resp:
                    resp_body = resp.read().decode("utf-8")
                    data = json.loads(resp_body)
                    granted = data.get("permissions", [])
                    missing = [p for p in req_perms if p not in granted]
                    has_sanitize = "modelarmor.templates.useToSanitizeUserPrompt" in granted
                    has_view = "modelarmor.templates.get" in granted

                    is_success = len(missing) == 0
                    err_msg = None
                    if not is_success:
                        err_msg = f"Missing prerequisite Model Armor permissions on project '{proj}': {', '.join(missing)}"

                    return {
                        "success": is_success,
                        "project_id": proj,
                        "status_code": resp.status,
                        "granted_permissions": granted,
                        "missing_permissions": missing,
                        "has_sanitize_permission": has_sanitize,
                        "has_view_permission": has_view,
                        "error_message": err_msg,
                    }
            except urllib.error.HTTPError as e:
                err_content = e.read().decode("utf-8", errors="ignore")
                last_error = f"HTTP {e.code}: {e.reason} - {err_content}"
                return {
                    "success": False,
                    "project_id": proj,
                    "status_code": e.code,
                    "granted_permissions": [],
                    "missing_permissions": req_perms,
                    "has_sanitize_permission": False,
                    "has_view_permission": False,
                    "error_message": last_error,
                }
            except Exception as e:
                last_error = str(e)

            time.sleep(0.1 * (2 ** attempt))

        return {
            "success": False,
            "project_id": proj,
            "status_code": 0,
            "granted_permissions": [],
            "missing_permissions": req_perms,
            "has_sanitize_permission": False,
            "has_view_permission": False,
            "error_message": f"Failed to test IAM permissions: {last_error}",
        }


