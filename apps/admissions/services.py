"""
Admissions domain services.

Keeps the convert-to-student action out of the view/serializer layer:
it's an atomic, multi-system operation (Keycloak user creation + local
Student record), not simple CRUD, and deserves its own testable unit.
"""

import logging

import requests
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from models import Application

logger = logging.getLogger(__name__)


class KeycloakAdminError(Exception):
    pass


class KeycloakAdminClient:
    """
    Thin wrapper around Keycloak's Admin REST API using the sims-backend
    confidential client's service account (client_credentials grant).

    Scope note: sims-backend currently holds realm-management's
    manage-users + view-users roles (Option A — accepted broad scope for
    MVP; see runbook for the FGAP-scoped alternative to revisit pre-prod).
    """

    def __init__(self):
        self.server_url = settings.KEYCLOAK_SERVER_URL.rstrip("/")
        self.realm = settings.KEYCLOAK_REALM
        self.client_id = settings.KEYCLOAK_BACKEND_CLIENT_ID
        self.client_secret = settings.KEYCLOAK_BACKEND_CLIENT_SECRET
        self._token = None

    def _get_service_account_token(self):
        resp = requests.post(
            f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=10,
        )
        if not resp.ok:
            raise KeycloakAdminError(f"Failed to obtain service account token: {resp.text}")
        return resp.json()["access_token"]

    def _headers(self):
        if self._token is None:
            self._token = self._get_service_account_token()
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def create_user(self, *, email: str, first_name: str, last_name: str, role: str) -> str:
        """Creates a disabled-password Keycloak user with a required action to
        set their own password on first login. Returns the Keycloak user UUID."""
        payload = {
            "username": email,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "emailVerified": False,
            "requiredActions": ["UPDATE_PASSWORD", "VERIFY_EMAIL"],
        }
        resp = requests.post(
            f"{self.server_url}/admin/realms/{self.realm}/users",
            json=payload,
            headers=self._headers(),
            timeout=10,
        )
        if resp.status_code == 409:
            raise KeycloakAdminError(f"Keycloak user already exists for email {email}")
        if not resp.ok:
            raise KeycloakAdminError(f"Failed to create Keycloak user: {resp.status_code} {resp.text}")

        # Keycloak returns the new user's location in the Location header, not the body
        location = resp.headers.get("Location", "")
        user_id = location.rstrip("/").split("/")[-1]
        if not user_id:
            raise KeycloakAdminError("Keycloak did not return a user id")

        self._assign_realm_role(user_id, role)
        return user_id

    def _assign_realm_role(self, user_id: str, role_name: str):
        role_resp = requests.get(
            f"{self.server_url}/admin/realms/{self.realm}/roles/{role_name}",
            headers=self._headers(),
            timeout=10,
        )
        if not role_resp.ok:
            raise KeycloakAdminError(f"Realm role '{role_name}' not found: {role_resp.text}")
        role_repr = role_resp.json()

        assign_resp = requests.post(
            f"{self.server_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
            json=[role_repr],
            headers=self._headers(),
            timeout=10,
        )
        if not assign_resp.ok:
            raise KeycloakAdminError(f"Failed to assign role {role_name}: {assign_resp.text}")

    def delete_user(self, user_id: str):
        """Compensating action if the local transaction fails after Keycloak
        user creation succeeded — see convert_application_to_student."""
        requests.delete(
            f"{self.server_url}/admin/realms/{self.realm}/users/{user_id}",
            headers=self._headers(),
            timeout=10,
        )


def convert_application_to_student(application: Application, admission_year: int) -> "apps.students.models.Student":
    """
    Atomic admissions -> student conversion.

    Order of operations matters here: Keycloak user creation happens OUTSIDE
    Django's DB transaction (it's a separate system, can't be rolled back by
    Postgres), so on any failure after that point we explicitly delete the
    Keycloak user to avoid an orphaned identity with no matching Student.

    Requires apps.students.Student to exist — this app only builds the
    call site; wire the actual model import once `students` is scaffolded.
    """
    if not application.is_convertible:
        raise ValueError(
            f"Application {application.id} is not convertible "
            f"(status={application.status}, already converted={hasattr(application, 'student')})"
        )

    Student = apps.get_model("students", "Student")
    User = apps.get_model(settings.AUTH_USER_MODEL.split(".")[0], settings.AUTH_USER_MODEL.split(".")[1])

    kc_client = KeycloakAdminClient()
    keycloak_user_id = kc_client.create_user(
        email=application.email,
        first_name=application.first_name,
        last_name=application.last_name,
        role="student",
    )

    try:
        with transaction.atomic():
            user = User.objects.create(
                email=application.email,
                first_name=application.first_name,
                last_name=application.last_name,
                role="student",
                sso_provider="keycloak",
                sso_uid=keycloak_user_id,
            )
            student = Student.objects.create(
                user=user,
                program=application.program,
                application=application,
                admission_year=admission_year,
                hall_code="00",
                status="active",
            )
            # ugc_id generation happens inside Student.save()/a signal per the
            # UGC identifier design doc — not duplicated here.
            return student
    except Exception:
        logger.exception(
            "Local conversion failed for application %s after Keycloak user %s was created — rolling back Keycloak user",
            application.id,
            keycloak_user_id,
        )
        kc_client.delete_user(keycloak_user_id)
        raise
