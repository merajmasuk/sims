# SIMS Backend

Student Information Management System (SIMS) backend for a Bangladesh university, built ahead of the university's first student intake. Covers the full student lifecycle — admissions → student records → enrollment → grading — with UGC (University Grants Commission) compliance and FERPA/GDPR-aware data handling.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Django 6.1 + Django REST Framework |
| Language runtime | Python 3.12+ |
| Database | PostgreSQL (single database, separate schemas) |
| Auth | Keycloak 26.7.2 (Docker), OIDC / JWT validation via JWKS |
| Config | `python-decouple` (`.env`-based) |
| Deployment (MVP) | Single VPS — Docker Compose, Gunicorn + Nginx |

**Explicitly out of scope for MVP:** Redis, Celery, Kubernetes, CDN, read replicas.

## Compliance Drivers

- **UGC (Bangladesh)** — mandatory identifier formats and admissions/records rules
- **FERPA / GDPR-awareness** — informs data handling even though the institution is neither US- nor EU-based
- **Strict on-premises data residency** — no cloud-hosted auth or data services; this is why Keycloak is self-hosted rather than using a cloud IdP

## Architecture Conventions

- **UUID7 primary keys** throughout, for time-ordered, non-enumerable identifiers
- **App naming:** `apps.<module>` (e.g. `apps.admissions`), referenced in `INSTALLED_APPS` via explicit `AppConfig` paths (e.g. `"apps.admissions.apps.AdmissionsConfig"`)
- **Settings split:** `config/settings/{base,local,production}.py`
- **`INSTALLED_APPS` composition:** built from `DJANGO_APPS` + `THIRD_PARTY_APPS` + `LOCAL_APPS` (not appended ad hoc), with `LOCAL_APPS` listing all eight apps upfront
- **Imports:** explicit absolute (`from apps.core.models import X`) or relative (`from .models import X`) — no bare module-name imports
- All eight apps have stub `apps.py` + empty `models.py` in place from project start, so the project boots cleanly at every stage of the build

## Modules

The system is organized into eight Django apps, built sequentially:

1. `core` — `Department`, `Program`, `AcademicTerm`
2. `users` — custom `User` model, Keycloak-backed auth/roles
3. `admissions` — `Application` model, review workflow, convert-to-student *(in progress)*
4. `students` — `Student` profile records
5. `faculty` — `FacultyProfile`
6. `academics` — `Course`, `CourseOffering`
7. `enrollment` — `Enrollment` (Student ↔ CourseOffering)
8. `grading` — `Grade`, linked to `Enrollment`

### Current status

- **Keycloak** — 26.7.2, running in Docker
- **`admissions`** — `Application` model (UUID7 PK, four-state workflow: `submitted → under_review → accepted/rejected`); separate public/staff/review serializers; `KeycloakAdminClient` service; `ApplicationViewSet` with public `create` and admin-only `review` / `convert` actions
- **`students`, `faculty`, `academics`, `enrollment`, `grading`** — stubbed, not yet built

## Authentication

- Keycloak owns credentials and identity; the Django `users` app is a profile/role layer on top
- Django validates Keycloak-issued JWTs against the JWKS endpoint
- Keycloak client `sims-backend` currently uses broad `manage-users` / `view-users` scope for MVP — **Fine-Grained Admin Permissions are deferred to pre-production hardening**

### Cross-system atomicity (Keycloak + DB)

Application-to-student conversion creates a Keycloak user as part of the workflow. Because Keycloak and PostgreSQL are separate systems, this cannot be wrapped in a single transaction:

- Keycloak user creation happens **outside** the DB transaction
- On failure after the Keycloak user is created, a **compensating delete** removes the Keycloak user to avoid orphaned accounts

## Database

- Single PostgreSQL database, with logical separation via **schemas** (app schema + Keycloak's own schema)
- Local/dev setup currently uses the `dynamic` Postgres role for Keycloak's schema (not a dedicated `keycloak_app` role) — acceptable for early development, **flagged to revisit before production**
- On PostgreSQL 15+, the `public` schema no longer grants `CREATE`/`USAGE` by default; these were granted explicitly to the `dynamic` role to resolve `permission denied for schema public`

> **Open item:** overall DB architecture (app data vs. Keycloak data storage/roles) is being revisited and is not final.

## Known Technical Debt

Documented deliberately here rather than deferred silently:

- Keycloak client permission scope is broad (`manage-users`/`view-users`); needs Fine-Grained Admin Permissions before production
- `dynamic` Postgres role is shared between app and Keycloak schema; dedicated role isolation for Keycloak is pending
- DB architecture (app vs. Keycloak data storage) is still an open design question

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Docker + Docker Compose (for Keycloak)

### Setup

```bash
# clone and enter the project
git clone <repo-url>
cd sims-backend

# create and activate a virtual environment
python3.12 -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# copy environment template and configure
cp .env.example .env
# edit .env with your DB credentials, Keycloak settings, etc.

# start Keycloak (and any other Docker services)
docker compose up -d

# run migrations
python manage.py migrate

# create a superuser (optional, for Django admin)
python manage.py createsuperuser

# run the development server
python manage.py runserver
```

### Environment Variables

Configuration is managed via `python-decouple` and a `.env` file. Key variables include database credentials, Keycloak realm/client settings, and the institution's UGC university code (kept in settings as an institution-level constant, not stored per-record in the database).

## Project Structure

```
sims-backend/
├── apps/
│   ├── core/
│   ├── users/
│   ├── admissions/
│   ├── students/
│   ├── faculty/
│   ├── academics/
│   ├── enrollment/
│   └── grading/
├── config/
│   └── settings/
│       ├── base.py
│       ├── local.py
│       └── production.py
├── manage.py
├── requirements.txt
└── .env.example
```

## Roadmap

- Finish building out `admissions`
- Build `students` (next module in sequence)
- Continue through `faculty` → `academics` → `enrollment` → `grading`
- Pre-production hardening: Keycloak Fine-Grained Admin Permissions, dedicated Postgres role for Keycloak, finalize DB architecture
