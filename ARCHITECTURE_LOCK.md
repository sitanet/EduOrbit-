# EduOrbit Enterprise Master Architecture Lock v1.0

> [!IMPORTANT]
> **GOVERNANCE OVERRIDE NOTICE**
> Before every implementation task, read this document (`ARCHITECTURE_LOCK.md`).
> These rules override all defaults. If a requested change conflicts with this document, **STOP and report the conflict** instead of generating code.

---

## 1. Architecture Lock (v1.0)
- Architecture Version: 1.0 (LOCKED)
- No new models
- No new folders
- No new services
- No renaming
- Only strict execution of the defined blueprint. Future improvements belong to Version 2.0.
- All other EduOrbit modules are **FROZEN**. HRPM is the **SINGLE ACTIVE MODULE**.

---

## 2. Database Lock (PostgreSQL Strictly)
- Engine: PostgreSQL (`django.db.backends.postgresql`)
- Do NOT create `sqlite3` databases.
- Do NOT reference `db.sqlite3`.
- Do NOT generate SQLite-specific SQL.
- Do NOT modify `DATABASES` to use `sqlite3`.
- All migrations target PostgreSQL engine.
- Use PostgreSQL features where appropriate (JSONB, ArrayField, GIN indexes, Full Text Search).

---

## 3. Technology Stack Lock
- **Backend**: Python 3.13, Django 5.x, PostgreSQL, Redis, Celery, Gunicorn, Nginx.
- **Forbidden**: SQLite, MySQL, MariaDB, and Django Admin for production features.

---

## 4. Existing Code Rule
- Before creating or modifying any file, inspect the existing implementation.
- Never regenerate: `settings.py`, `urls.py`, `models.py`, `apps.py`, `admin.py`, or `migrations`.
- Reuse existing classes, models, services, serializers, permissions, and utilities whenever possible.
- Existing code always takes precedence over generated code.

---

## 5. Migration Policy
- Never delete existing migrations.
- Never reset migration history.
- Never squash migrations unless explicitly instructed.
- Generate incremental PostgreSQL migrations only.
- Preserve production data.

---

## 6. Repository Inspection Rule
Before implementing any feature, inspect:
- `settings/`
- `pyproject.toml` / `requirements.txt`
- Environment configuration
- Existing models, migrations, services, serializers, ViewSets, selectors, validators, permissions, templates, and tests.
- Do not assume project structure. Extend only what already exists.

---

## 7. PostgreSQL Verification Rule
Before creating migrations or executing tests:
- Verify `ENGINE = django.db.backends.postgresql`
- Verify `NAME`, `USER`, `HOST`, and `PORT` are PostgreSQL values.
- Never generate or use `db.sqlite3`.
- Never execute SQLite migrations or emit SQLite SQL.

---

## 8. Production Data Rule (Zero Mock Data)
- No mock arrays.
- No placeholder services.
- No fake repositories.
- No temporary implementations.
- No TODO business logic.
- Every screen must read from the database or approved seed data.

---

## 9. Module Integration Rule
Before implementing any HR feature:
1. Check whether another EduOrbit module already provides the functionality.
2. Reuse that module.
3. Integrate through public interfaces.
4. Do not duplicate business logic.

---

## 10. 13 Measurable Slice Certification Exit Criteria

A Vertical Slice is certified **100% COMPLETE** only if:
1. ✅ Domain models implemented & validated
2. ✅ Incremental PostgreSQL migrations created & applied
3. ✅ Write services implemented with `@transaction.atomic`
4. ✅ Read selectors implemented for performant queries
5. ✅ Validators implemented for business integrity
6. ✅ 8-Tier RBAC permissions enforced
7. ✅ REST APIs implemented under `/api/v1/hr/`
8. ✅ HTMX web views rendered with real DB data (zero mock data)
9. ✅ Domain events published to `event_bus`
10. ✅ Inter-module integrations functioning
11. ✅ Automated unit, API & integration tests passing
12. ✅ Independent seed command verified
13. ✅ Documentation updated & code reviewed against governance rules
