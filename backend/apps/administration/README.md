# Enterprise School Administration & Super Admin Control Center (ESSACC) Documentation

This document describes the platform settings, school settings, subscription plans, module licenses, feature flags overrides, white-label brandings, immutable audits logs, and developer API keys of the **administration** app.

---

## 1. Subscriptions & Licensing
- **SubscriptionPlan**: Packages configuration (pricing, student limits).
- **SchoolSubscription**: Active subscribers status tracks.
- **ModuleLicense**: Seat licensing flags.

---

## 2. White-Labeling Overrides
- **SchoolSetting & SchoolBranding**: Color styles and custom domain mapping.
- **FeatureFlag**: Dynamic feature toggles.

---

## 3. Auditing & API Integration
- **PlatformAudit**: Global operations audit trails.
- **APIKey**: Security integration tokens.

---

## 4. REST APIs
Endpoints are mapped under `/administration/api/v1/`:
- `GET/POST /administration/settings/`: Platform settings.
- `GET/POST /administration/licenses/`: Enabled module licenses.
- `GET/POST /administration/apikeys/`: Developer API keys.
