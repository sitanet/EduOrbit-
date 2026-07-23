# EduOrbit Enterprise Developer Documentation

Welcome to the official developer documentation for the **EduOrbit Multi-Tenant School Management System**. This document describes our standards, architecture, coding guidelines, and directory layouts.

---

## 1. Directory Layout

The workspace is organized into three major sections:
- **`backend/`**: Django 5 core setting, applications, components, layouts, and public static properties.
- **`mobile/`**: Feature-partitioned Clean Architecture Flutter mobile layout.
- **`integrations/`**: Module adapters decoupling third-party payment, SMS, email, AI, and ERP structures from core views.

---

## 2. Naming & Coding Conventions

- **Python (PEP 8)**: Use standard `snake_case` for methods, variable definitions, and database models. Use `CamelCase` for Services, Forms, Views, and Models classes.
- **JavaScript (ES2025)**: Modular class files using `camelCase` parameters. No global namespace pollutions.
- **Dart (Effective Dart)**: Proper file suffixes (e.g. `_widget.dart`, `_bloc.dart`) and strong types.
- **HTML / CSS**: Kebab case naming for styling rules matching MD3 design tokens.

---

## 3. Core Architecture Decisions

### Clean Architecture with Service Layer
Views (delivery layer) must be thin. They receive requests, bind configurations, and invoke Services to execute mutation actions.
```python
# Create student workflow
CreateStudentService.execute(tenant_id=tenant_id, data=payload)
```

### Row-level Tenant Isolation
Every database model inherits from `TenantBaseModel`. Database lookups filter using Django's default `TenantManager`, preventing leakage of school data between tenant instances.

---

## 4. API Conventions

All JSON-based web services follow the envelope format:
- **Success Response**: `{"success": true, "data": {...}, "meta": {"timestamp": "..."}}`
- **Error Response**: `{"success": false, "error": {"code": "...", "message": "..."}, "meta": {"timestamp": "..."}}`

---

## 5. Development Workflow & Git Strategy

- **Branching**: Follow Git Flow. Use prefixes: `feature/` for additions, `bugfix/` for corrections, `hotfix/` for emergency corrections.
- **Commits**: Follow conventional commits: `feat: add core audit tracking`, `fix: tenant middleware subdomain check`.
- **Testing**: Before submitting any PR, all unit and API tests must pass:
  ```bash
  python backend/manage.py test
  ```
