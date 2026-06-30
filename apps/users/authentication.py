import logging
import threading
import time

import jwt
import requests
from django.conf import settings
from rest_framework import authentication, exceptions

from users.models import LoginAuditLog, User

logger = logging.getLogger(__name__)


class JWKSCache:
    """
    Thread-safe in-memory cache for Keycloak's JWKS (JSON Web Key Set).

    No Redis for MVP — this is a deliberate single-process cache. Fine for a
    single-VPS deployment; would need to move to a shared cache (Redis) if
    Django ever runs as multiple processes/workers without sticky JWKS state,
    since each worker would otherwise fetch independently (acceptable, just
    slightly redundant — not a correctness issue).
    """

    def __init__(self, jwks_url: str, ttl_seconds: int = 300):
        self._jwks_url = jwks_url
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._cached_jwks = None
        self._fetched_at = 0.0

    def get_jwks(self) -> dict:
        now = time.monotonic()

        # Fast path: cache is warm, no lock needed for the read.
        if self._cached_jwks is not None and (now - self._fetched_at) < self._ttl:
            return self._cached_jwks

        with self._lock:
            # Re-check inside the lock in case another thread refreshed
            # while we were waiting.
            now = time.monotonic()
            if self._cached_jwks is not None and (now - self._fetched_at) < self._ttl:
                return self._cached_jwks

            response = requests.get(self._jwks_url, timeout=5)
            response.raise_for_status()
            self._cached_jwks = response.json()
            self._fetched_at = now
            return self._cached_jwks

    def get_signing_key(self, kid: str):
        jwks = self.get_jwks()
        for key in jwks.get('keys', []):
            if key.get("kid") == kid:
                return jwt.PyJWK(key)

        # kid not found — could mean Keycloak rotated keys. Force a refresh
        # once before giving up, in case our cache is just stale.
        with self._lock:
            self._cached_jwks = None
            self._fetched_at = 0.0
        jwks = self.get_jwks()
        for key in jwks.get('keys', []):
            if key.get("kid") == kid:
                return jwt.PyJWK(key)

        return None


_jwks_cache = JWKSCache(
    jwks_url=settings.KEYCLOAK_JWKS_URL,
    ttl_seconds=getattr(settings, 'KEYCLOAK_TTL_SECONDS', 300),
)


class KeycloakJWTAuthentication(authentication.BaseAuthentication):
    """
    Validates Keycloak-issued JWTs against the realm's JWKS endpoint and
    resolves them to a pre-provisioned Django User via `keycloak_uid`.

    Deliberately does NOT auto-create users. SIMS accounts are provisioned
    through admissions/HR workflows, not self-registration — a valid token
    for an unknown `sub` is a 403, not an account creation event.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header or not auth_header.startswith(f"{self.keyword} "):
            return None

        token = auth_header.split(" ", 1)[1].strip()
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.PyJWTError:
            raise exceptions.AuthenticationFailed("Malformed token.")

        kid = unverified_header.get("kid")
        signing_key = _jwks_cache.get_signing_key(kid) if kid else None
        if signing_key is None:
            raise exceptions.AuthenticationFailed("Unable to resolve signing key for token.")

        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["HS256"],
                audience=settings.KEYCLOAK_AUDIENCE,
                issuer=settings.KEYCLOAK_ISSUER,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.ExpiredSignatureError:
            self._log_login(
                user=None,
                keycloak_uid=self._extract_sub_unsafe(token),
                ip_address=ip_address,
                user_agent=user_agent,
                action=LoginAuditLog.Action.TOKEN_EXPIRED,
            )
            raise exceptions.AuthenticationFailed("Token has expired.")
        except jwt.PyJWTError as exc:
            logger.warning("JWT validation failed: %s", exc)
            raise exceptions.AuthenticationFailed("Invalid token.")

        keycloak_uid = payload.get("sub")
        if not keycloak_uid:
            raise exceptions.AuthenticationFailed("Token missing 'sub' claim.")

        try:
            user = User.objects.get(keycloak_uid=keycloak_uid)
        except User.DoesNotExist:
            self._log_login(
                user=None,
                keycloak_uid=keycloak_uid,
                ip_address=ip_address,
                user_agent=user_agent,
                action=LoginAuditLog.Action.LOGIN_FAILED,
            )
            raise exceptions.PermissionDenied(
                "No account is provisioned for this identity. Please contact your administrator."
            )

        if not user.is_active:
            self._log_login(
                user=user,
                keycloak_uid=keycloak_uid,
                ip_address=ip_address,
                user_agent=user_agent,
                action=LoginAuditLog.Action.LOGIN_FAILED,
            )
            raise exceptions.AuthenticationFailed("This account has been deactivated.")

        self._sync_role(user, payload)

        # Only log on session start, not every request. We treat "session
        # start" as: the client has signaled this is a fresh login via the
        # custom header set by the frontend's OIDC callback handler.
        if request.META.get("HTTP_X_SIMS_LOGIN_EVENT") == "1":
            self._log_login(
                user=user,
                keycloak_uid=keycloak_uid,
                ip_address=ip_address,
                user_agent=user_agent,
                action=LoginAuditLog.Action.LOGIN_SUCCESS,
            )
        return user, token

    def authenticate_header(self, request):
        return self.keyword

    @staticmethod
    def _extract_sub_unsafe(token: str) -> str:
        """Best-effort extraction of 'sub' from an expired/unverified token, for audit logging only."""
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            return unverified.get("sub", "")
        except jwt.PyJWTError:
            return ""

    @staticmethod
    def _sync_role(user: User, payload: dict) -> None:
        """
        Syncs the Django user's role from the JWT's realm_access.roles claim.
        Only writes to the DB if the role actually changed.
        """
        roles = payload.get("realm_access", {}).get("roles", [])
        role_priority = [User.Role.ADMIN, User.Role.FACULTY, User.Role.STUDENT]

        matched_role = next((r for r in role_priority if r.value in roles), None)
        if matched_role and user.role != matched_role:
            user.role = matched_role
            user.save(update_fields=["role"])

    @staticmethod
    def _get_client_ip(request) -> str:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    @staticmethod
    def _log_login(*, user, keycloak_uid, ip_address, user_agent, action):
        try:
            LoginAuditLog.objects.create(
                user=user,
                keycloak_uid=keycloak_uid or "",
                ip_address=ip_address or "0.0.0.0",
                user_agent=user_agent,
                action=action,
            )
        except Exception:
            logger.exception("Failed to write LoginAuditLog entry.")
