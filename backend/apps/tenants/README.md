# EduOrbit Tenant Lifecycle Management (TLM) System Documentation

This document describes the structure, provisioning sequence, billing models, and subscription mechanics of the **tenants** module.

---

## 1. TLM Architecture & Organization Structure
The architecture isolates corporate groups from individual schools:
- **Tenant (Organization)**: Platform-wide entity representing the educational organization (e.g. Grace Education Group).
- **School**: Scoped to Tenant (inheriting from `TenantBaseModel`). Represents the actual school (e.g. Grace Nursery School, Grace College).
- **Campus**: Scoped to School, containing location address details.
- **Branch**: Scoped to Campus.

---

## 2. Onboarding & Provisioning Flow

```
[ Wizard Post Request ] ──> [ TenantOnboardingService.onboard_organization() ]
                                  │
                                  ├─> [ 1. Create Tenant (Org) ]
                                  ├─> [ 2. Create School ]
                                  ├─> [ 3. Register Administrator User ]
                                  ├─> [ 4. Map Admin TenantMembership ]
                                  ├─> [ 5. Activate 30-day Free Trial ]
                                  ▼
                        [ Emit events & Audit logs ]
```

---

## 3. Subscription & Module-Based Billing Models
We support three dynamic billing models at the Tenant level:
1. **Model A (School Pays)**: School pays base subscription, parents do not pay system access fees.
2. **Model B (Parents Pay)**: Parents pay access transactions directly, school pays no base subscription.
3. **Model C (Hybrid Billing)**: School pays base subscription, parents pay for premium services (AI Tutor, Transport, etc.).

Module licenses are controlled dynamically inside `TenantSubscription.modules_licensed` (e.g. enabling `ai_assistant`, `hostel`, `clinic` independently).

---

## 4. REST APIs
The endpoints are mounted under `/tenants/api/v1/`:
- `POST /tenants/onboard/`: Provision Tenant, School, Admin account, and trial plan.
- `GET/POST /tenants/campuses/`: Lists and adds campuses.
- `POST /tenants/domains/<uuid>/verify/`: Mock DNS verification check.
