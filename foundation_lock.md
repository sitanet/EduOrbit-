# EduOrbit Core Foundation Lock Specification (v1.0.0)

This document freezes the platform architecture, technical core, Identity & Access Management (IAM) framework, Tenant Lifecycle Management (TLM) structure, Academic Configuration Engine (ACE), People Management Core (PMC), Admissions & Enrollment Management (AEM), Student Lifecycle Management (SLM), Timetable & Scheduling Engine (TSE), Teacher Workspace Core (TWC), Attendance Management (ATM), Learning Management System (LMS), Enterprise Assessment Engine (EAE), Enterprise Examination Management & Results Processing (EMRP), Enterprise Finance, Fees & Billing Management (EFBM), Enterprise Communication & Engagement Hub (CEH), Enterprise Human Resources & Payroll Management (HRPM), Enterprise Library Management System (ELMS), Enterprise Transport & Fleet Management (ETFM), Enterprise Hostel & Residential Management (EHRM), Enterprise Clinic, Health & Medical Management (ECHM), Enterprise Inventory, Procurement & Asset Management (EIPAM), Enterprise Workflow, Documents & Approval Engine (EWDAE), Enterprise Facilities, Maintenance & Work Orders (EFMWO), Enterprise Analytics, Business Intelligence & AI Decision Support (EABI), Enterprise Parent, Student & Staff Self-Service Portal (EPSSP), Enterprise School Administration & Super Admin Control Center (ESSACC), Enterprise AI Platform & Automation Engine (EAPAE), Enterprise Flutter Mobile Platform (EMFP), Enterprise UI/UX Completion, Enterprise Production Infrastructure & DevOps (EPID), and Enterprise Certification & QA (ECR) setups. No structural modifications, deletions, or shifts in these base definitions may occur without explicit instruction.

---

## 1. Context Resolution & Routing
- **Enforcement**: Active school tenant context is resolved inside `TenantMiddleware` and bound to the thread/async state using `contextvars.ContextVar('current_tenant')`.
- **Target**: Safe for both WSGI and ASGI (WebSockets & Channels) request lifecycles.

## 2. Base Model Layer Schema
- **PlatformBaseModel**: For global data tables not constrained by school instances (plans, curricula, locations).
- **TenantBaseModel**: For isolated data tables requiring an explicit ForeignKey pointer mapping to `tenants.Tenant`. Enforces global managers excluding soft-deleted rows.

## 3. Dependency Injection Container (IoC)
- **Container**: Register all components and adapters mapping interfaces to concrete implementations in `core/di.py` using `ioc.register()`.
- **Reference**: Always resolve using `ioc.resolve(IInterfaceName)`. Never import concrete implementation adapters directly into business logic views or service layers.

## 4. Module Registry Strategy
- **Registry**: Optional modules register using `ModuleMetadata` configurations. Enables platform-wide feature toggling without altering core schemas.

## 5. Unified Domain Event & Notification Buses
- **Event Bus**: Publishes standard system notifications (`DomainEvent`) to sync listeners and routes async processing jobs to Celery.
- **Notification Bus**: Aggregates outbound messaging pipelines (Email, SMS, Push, WhatsApp, WebSockets) under a polymorphic interface.

## 6. Enterprise Audit Log Trail
- **Structure**: Captures row-level state changes (`before_state` vs `after_state` JSON diffs) and client request details (browser, device, IP).

## 7. Identity & Access Management (IAM) Lock
- **Custom User Base**: Pluggable account profiles are global (`User` inherits from `AbstractBaseUser` and platform properties) mapping to multiple tenants via `TenantMembership`.
- **RBAC Matrix**: Permissions are data-driven containing categories, modules, and toggles (Permission -> PermissionGroup -> Role -> RoleGroup).
- **Password History**: Restricts reuse against the last 5 passwords using Django's native password hashing framework (`check_password`). Storing or utilizing raw/MD5 passwords is strictly forbidden.
- **Device Trust & Sessions**: User device metadata and fingerprints are stored and auditable in `UserSession`.
- **Pluggable Authentication**: Authentication routes resolve through `IAuthenticationProvider` interfaces registered in `auth_provider_registry`.

## 8. Tenant Lifecycle Management (TLM) Lock
- **Tenant vs School Split**: `Tenant` acts as corporate group (Organization). `School` represents specific institutional entities mapped under the Tenant via `TenantBaseModel` (inherits tenant ForeignKey).
- **Multi-Campus / Branches**: `Campus` scopes to School. `Branch` scopes to Campus.
- **Module Licensing**: Subscriptions map to `TenantSubscription` containing modular feature parameters inside `modules_licensed` (e.g. enabling `ai_assistant`, `hostel` independently).
- **Billing Models**: Configured at Tenant profile level supporting Model A (School Pays), Model B (Parents Pay), and Model C (Hybrid Billing).
- **Domain Verification**: Restricts custom web traffic to whitelisted domains validated via CustomDomain verification tokens.

## 9. Academic Configuration Engine (ACE) Lock
- **Hierarchy Mapping**: Isolates academic metadata by linking AcademicYear, EducationLevel, AcademicLevel, and AcademicClass models to unique School ForeignKey IDs.
- **Subject Offering System**: Subjects attach to global `Curriculum` objects, and active assignments to classes are handled dynamically through `SubjectOffering`.
- **Multi-Scheme Grading**: GradingScale support is assignable by school and level. Assessment weights are configured through structured percentages in `AssessmentComponent`.
- **Calendar & Resource Management**: School calendar schedules support recurrences, and classroom room models catalog lab/hall details under `AcademicResource`.

## 10. People Management Core (PMC) Lock
- **Polymorphic Person Profiles**: All demographic properties are stored in a central base table (`Person` inheriting from `TenantBaseModel` and mapped optionally to IAM `User`).
- **Role Assignment Engine**: Explicit roles (`student`, `teacher`, `parent`, `staff`) are assigned in `PersonRole` mapping to specific schools/campuses, allowing multiple active roles per Person.
- **Normalized Contacts**: EmailAddress, PhoneNumber, PhysicalAddress, and EmergencyContact tables isolate contact types with verified and primary status flags.
- **Junction Family Linkage**: FamilyRelationship maps student-parent relations including pickup, fee responsibility, custody, and emergency priorities.
- **Medical & Qualifications logs**: Medical profile and visits logs, and certifications/employment histories are tracked under independent child tables.

## 11. Admissions & Enrollment Management (AEM) Lock
- **Applicant Registry**: `Applicant` maps back to `Person` core records, allowing multiple applications under distinct campaigns.
- **Intake Cohort Scoping**: Mapped via `AdmissionCampaign` (school-level campaign periods) and nested `AdmissionIntake` cohorts.
- **Generic Forms Engine**: FormDefinition, FormSection, FormField, and FormSubmission create dynamic layouts reusable across other system plugins.
- **Verification & Assessment**: Tracked via `ApplicationDocument` status codes and `AdmissionAssessment` marks logs.
- **Waitlist & Offer lifecycle**: Tracked via `AdmissionWaitlist` queues and `AdmissionOffer` deadlines.
- **Transactional Promotions**: Prompts atomic generation of `StudentProfile` profiles and assignment codes during student registrations.

## 12. Student Lifecycle Management (SLM) Lock
- **State Machine Transitions**: Student status cycles are validated via `StateMachine` configurations and logged in `StudentStatusHistory`.
- **Permanent Placements History**: Placements are archived sequentially in `AcademicPlacementHistory` to retain complete class records over terms.
- **Clubs & School Houses**: Custom color and captain metrics are stored in `SchoolHouse` and member records in `StudentClubMembership`.
- **Student Timeline Log**: Timeline records in `StudentTimeline` aggregate student activities (discipline, warning, promotions) chronologically.

## 13. Timetable & Scheduling Engine (TSE) Lock
- **Generic Scheduling Entity**: `Schedule` maps events, lessons, and bookings uniformly utilizing global `ScheduleType` selectors.
- **Resource Management Capacity**: physical assets (buses, ICT rooms, science labs) enforce capacity boundaries and availability blocks in `Resource`.
- **Multi-Level Bell Timings**: Configured via school-scoped `BellSchedule` groups and child timing slots in `TimeSlot`.
- **Conflict Tracking Logs**: DB-driven overlapping warning states are stored and resolved in `ConflictReport` logs.
- **Structural Lesson Isolation**: Class teaching parameters (Teacher, Class, Subject) are defined separately in `Lesson` before slot assignment.

## 14. Teacher Workspace Core (TWC) Lock
- **Four-Layer Lesson Architecture**: Mapped dynamically utilizing `Curriculum` versions, `SchemeOfWork` term plans, `WeeklyPlan` subdivisions, and `LessonPlan` guides.
- **Slotted Lesson Instances**: Decouples study plans from schedules via `LessonInstance` and `LessonDelivery` trackers.
- **Richer Assignments & Observables**: Class homework, projects, and reading tasks are mapped in `Assignment`, and student timeline feedback in `StudentObservation`.
- **Teaching Journals**: Daily logs (delivered classes, reflection topics) are indexed in `TeachingJournal`.
- **AI Extension Hooks**: Abstract interfaces (`IAILessonPlanner`, `IAIHomeworkGenerator`, `IAITeachingCoach`) decouple future generative plug-ins.

## 15. Attendance Management (ATM) Lock
- **Polymorphic Logging Engine**: `AttendanceRecord` maps any verified `Person` (student, teacher, bus driver) to single `AttendanceSession` metrics.
- **Richer Policy Rules**: Configured via school-scoped `AttendancePolicy` (grace periods, rules).
- **Physical Device Nodes**: biometrics terminals register parameters in `AttendanceDevice`.
- **Pickup Verification**: authorized parents and pins validations are tracked under `ParentPickup`.
- **Offline Synced Queues**: local client caches are queued inside `OfflineSyncQueue` to resolve intermittent connection sync actions.
- **AI Analytics Extension stubs**: interfaces (`IAIAttendanceRiskAnalyzer`, `IAIAbsenteeismPredictor`, `IAIStudentWellbeingDetector`) are registered in the DI container.

## 16. Learning Management System (LMS) Lock
- **Three-Tier Course Structure**: Curriculum items are organized hierarchically under `LearningModule` headers, `LearningUnit` pages, and versioned `LearningContent` / `LearningActivity` checkouts.
- **DRM Content Permissions**: Access controls (downloads, streaming restrictions, device limits, printing permissions) are defined under `ContentLicense`.
- **Gamification Metrics**: Achievements records (Badges, Points ledger) are saved inside `StudentBadge` and `StudentPoints`.
- **Student Progress History**: Time logs and completion percent values, active learning times, pauses count, and offline sync parameters are catalogued in `StudentProgress`.
- **Digital Library & Index**: Shared repository metadata is stored in `DigitalLibraryResource`, search filters in `LearningSearchIndex`, and zip files manifest in `OfflinePackage` / `OfflineManifest`.
- **Pluggable AI Extensions**: Abstract tutor and content generator interfaces (`IAIContentGenerator`, `IAILessonSummarizer`, `IAIFlashcardGenerator`, `IAILearningPathGenerator`, `IAIRecommendationEngine`) decouple future AI services.

## 17. Enterprise Assessment Engine (EAE) Lock
- **Polymorphic Delivery Framework**: Supports modular delivery mappings (CBT attempt portal, printed physical copies generation) using the same underlying `Question` and `QuestionChoice` entities.
- **Blueprint Selection Logic**: Auto-generates examination instances from question pools based on target topics, weights, and complexity ratios in `AssessmentBlueprint`.
- **Proctor Security Logging**: Captures browser window deviations, copy/paste attempts, and network shifts under `ProctorLog`.
- **Evaluation Rubrics Registry**: Caches manual evaluation steps and grading feedback in `Rubric` and `RubricCriteria`.
- **Marking & Caching Engine**: MCQ check-ins trigger atomic grading calculations inside `AutoMarkAPIView` and results caching in `AssessmentResult`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIQuestionGenerator`, `IAIDistractorGenerator`, `IAIQuestionReviewer`, `IAIAssessmentBuilder`, `IAIMarkingAssistant`, `IAIIntegrityAnalyzer`) decouple future LLM proctoring analysis.

## 18. Enterprise Examination Management & Results Processing (EMRP) Lock
- **Official Examination Scheduling**: Coordinates classroom exams venue allocations and student registrations using `ExamSession`, `Examination`, `CandidateRegistration`, and `SeatingArrangement`.
- **Weighted Formula Grading Engine**: Implements data-driven score calculators evaluating python grading expressions (e.g. `raw_score * 0.7 + 30`) through `GradingFormula`.
- **Version Controlled Results Pipeline**: Caches results details, approvals status, modification correction logs, and previous records lists inside `ExamResult`, `ResultVersion`, and `ResultCorrection`.
- **Transcript & Promotions Preview**: Maintains flat cached GPAs and cumulative student averages inside `AcademicRecord` and `CumulativeRecord` to facilitate digital signs off.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIResultAnalyzer`, `IAIRemarkGenerator`, `IAIPromotionAdvisor`, `IAIPerformancePredictor`, `IAITranscriptAdvisor`, `IAIRiskDetector`) are registered in the DI container.

## 19. Enterprise Finance, Fees & Billing Management (EFBM) Lock
- **Multi-Tenant Invoicing**: Manages invoice items allocations and outstanding balances tracking using `FeeStructure`, `FeeRule`, `Invoice`, and `InvoiceItem`.
- **Double-Entry General Ledger Event Sourcing**: Posts balanced debits/credits records mapping to receivables or cash accounts in `JournalEvent`, `JournalEntry`, and `LedgerPosting`.
- **Auditable Payments & Parent Wallets**: Pre-paid parent account fundings and refunds requests are verified using `StudentWallet`, `WalletTransaction`, and `RefundRequest`.
- **SaaS Subscription Billing**: Tracks platform corporate commission shares and subscription invoices inside `TenantSubscriptionInvoice` and `PlatformCommission`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIPaymentPredictor`, `IAIDefaulterPredictor`, `IAIRevenueAnalyzer`, `IAIFeeOptimizer`, `IAIScholarshipAdvisor`, `IAIFraudDetector`) are registered in the DI container.

## 20. Enterprise Communication & Engagement Hub (CEH) Lock
- **Polymorphic Omnichannel Messaging**: Dispatches universal message items and template substitutions using `Announcement`, `Notification`, and `NotificationPreference`.
- **Broadcast Campaigns Analytics**: Evaluates open rates and target audience parameters inside `BroadcastCampaign` and `CampaignAnalytics`.
- **Secure Messaging Chats**: Parent-Teacher message threads, RSVP check-ins, and survey polls are saved inside `Conversation`, `Message`, `EventRegistration`, and `Survey`.
- **Immutable Transaction Logs**: Stores gateway tracking status results sequentially in `CommunicationLog`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIAnnouncementWriter`, `IAITranslator`, `IAIMessageRewriter`, `IAISummarizer`, `IAIAutoResponder`, `IAISentimentAnalyzer`) are registered in the DI container.

## 21. Enterprise Human Resources & Payroll Management (HRPM) Lock
- **Polymorphic Person Profiles Linkage**: Links base `Person` records to `EmployeeProfile` mappings without duplicate demographic databases.
- **Leaves Approvals Engine**: Calculates time off balances dynamically using `LeaveRequest` and `LeaveBalance` tracking allowed/remaining limits.
- **Balanced Monthly Payroll Run**: Processes periods runs, gross earnings, and deductions using `PayrollPeriod`, `SalaryStructure`, and `PayrollRun`.
- **Performance Evaluation scores**: Logs appraisal scores in `PerformanceReview` and CPD certifications inside `TrainingProgram`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIResumeReviewer`, `IAIInterviewAssistant`, `IAIPayrollAuditor`, `IAIPerformanceCoach`, `IAITrainingAdvisor`, `IAILeavePredictor`) are registered in the DI container.

## 22. Enterprise Library Management System (ELMS) Lock
- **OPAC Bibliographic Cataloging**: Stores authors, publishers, and titles classifications mapping unique barcodes in `BookCopy` and locations in `Library`.
- **Dynamic Lending Policies**: Resolves loan days, max checkouts, and daily fines based on borrower user roles using `BorrowingPolicy`.
- **Auditable Circulation Engine**: Records loans checkout timelines, reservations holds queues, and accrued overdue fines using `BookIssue` and `BookReservation`.
- **Digital Library DRM**: Restricts download frequencies and types on worksheets or eBooks using `DigitalResource`.
- **Student Reading Engagement Progress**: Connects challenge goals to page-read increments using `ReadingChallenge` and `ReadingProgress`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIBookRecommendation`, `IAICatalogAssistant`, `IAIReadingCoach`, `IAIResourceClassifier`) are registered in the DI container.

## 23. Enterprise Transport & Fleet Management (ETFM) Lock
- **Hierarchical Passenger Assignment**: Tracks route check-ins (`TripPassenger`) attached to specific `Trip` runs and route pickup stops (`RouteStop`), bypassing direct vehicle links.
- **Fleet Asset Registry**: Registers physical school buses and driver licenses details using `Vehicle`, `VehicleCategory`, and `Driver`.
- **Live GPS Telemetry Log**: Caches live tracking coordinates, speeds, and timestamps inside `VehicleLocation`.
- **Fleet Operations Ledger**: Audits refuelings, service logs, and maintenance alerts using `FuelLog` and `MaintenanceSchedule`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIRouteOptimizer`, `IAIFuelPredictor`, `IAIArrivalPredictor`, `IAIDriverBehaviorAnalyzer`) are registered in the DI container.

## 24. Enterprise Hostel & Residential Management (EHRM) Lock
- **Bed Occupancy Constraints**: Allocates students to specific beds (`HostelBed`) which map to rooms (`HostelRoom`) and buildings (`Hostel`), preventing double-allocations.
- **Daily Curfew roll-calls**: Tracks evening attendance records and curfews using `HostelRollCall`.
- **Visitors & Incidents Logs**: Registers guest check-in/out timestamps and behavior warnings using `HostelVisitor` and `HostelIncident`.
- **Room Hygiene Appraisals**: Evaluates cleanliness scores using `RoomInspection`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIRoomAllocator`, `IAIOccupancyPredictor`, `IAIMaintenancePredictor`, `IAIDisciplineAnalyzer`) are registered in the DI container.

## 25. Enterprise Clinic, Health & Medical Management (ECHM) Lock
- **Patient Profiles Directory**: Connects base institution `Person` models to clinical classifications (`PatientProfile`) including chronic conditions, allergies, and blood groups.
- **Triage Consultation Workspace**: Registers check-in waitlists (`Appointment`) and symptoms consultations triage logs (`ClinicVisit`).
- **Pharmacy Batch Inventory**: Controls reorder levels and expiry limits on pharmacy drugs using `Drug` and `DrugBatch`.
- **Sick Bay In-patient Admissions**: Oversees sickbay ward bed assignments (`SickBayAdmission` and `Ward`).
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIDiagnosisAssistant`, `IAITriageAssistant`, `IAIMedicationInteractionChecker`, `IAIHealthRiskPredictor`) are registered in the DI container.

## 26. Enterprise Inventory, Procurement & Asset Management (EIPAM) Lock
- **Central Material Procurement**: Controls vendor directory profiles (`Supplier`), procurement requests (`PurchaseRequest`), and outbound orders (`PurchaseOrder`).
- **Warehouse Storage Management**: Manages stock itemsSku (`InventoryItem`), batch trackers (`InventoryBatch`), and movements ledger logs (`StockMovement`).
- **Capital Asset Registries**: Logs fixed assets list (`Asset` and `AssetCategory`), straight-line depreciation runs (`AssetDepreciation`), and servicing dates (`AssetMaintenance`).
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIPurchasePredictor`, `IAIStockForecast`, `IAIAutoReorder`, `IAISupplierEvaluator`) are registered in the DI container.

## 27. Enterprise Workflow, Documents & Approval Engine (EWDAE) Lock
- **Workflow & Version Orchestration**: Configured templates (`WorkflowDefinition`), version controls (`WorkflowVersion`), and sequential stages (`WorkflowStep`) to manage approvals across all applications.
- **Approval Engine Runtime**: Implemented running instance tracks (`WorkflowInstance`), task items (`WorkflowTask`), signature audits (`WorkflowApproval`), and role bypass configurations (`ApprovalDelegation`).
- **Document Repository**: Structured cloud storage pointers (`Document`) and revision backups (`DocumentVersion`).
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIWorkflowOptimizer`, `IAIApprovalPredictor`, `IAIDocumentClassifier`, `IAISLAAdvisor`) are registered in the DI container.

## 28. Enterprise Facilities, Maintenance & Work Orders (EFMWO) Lock
- **Physical Layouts & Assets Map**: Registers school properties, room numbers, and facility appliances using `Building`, `Floor`, `Room`, and `Facility`.
- **Work Order Engine**: Dispatches maintenance issues using `WorkRequest`, `WorkOrder`, and `WorkLog`.
- **Preventive Maintenance Schedules**: Generates recurrent check-ups using `FacilityMaintenancePlan` and `FacilityMaintenanceSchedule`.
- **Utilities Usage Metrics**: Reads energy/water consumption levels using `UtilityMeter` and `UtilityReading`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIMaintenancePredictor`, `IAIFacilityHealthAnalyzer`, `IAIEnergyOptimizer`, `IAIWorkOrderPrioritizer`) are registered in the DI container.

## 29. Enterprise Analytics, Business Intelligence & AI Decision Support (EABI) Lock
- **Dynamic Dashboard Configuration**: Maps custom view dashboards and visual parameters using `Dashboard` and `DashboardWidget`.
- **Key Performance Indicators & OLAP Cubes**: Computes aggregations, schedules, and calculations caches using `KPI`, `AnalyticsSnapshot`, and `DataCube`.
- **Executive Reporting Pipelines**: Defines templates and stores run outputs using `ReportDefinition` and `ReportExecution`.
- **AI Decision Forecasts**: Evaluates dropout and fee-default probability risks using `PredictiveInsight`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIPredictiveAnalytics`, `IAIAcademicAdvisor`, `IAIFinancialForecaster`, `IAIExecutiveNarrator`, `IAIDropoutPredictor`) are registered in the DI container.

## 30. Enterprise Parent, Student & Staff Self-Service Portal (EPSSP) Lock
- **Portals Layouts Mappings**: Configures custom theme choices, timezone values, and visual indicators using `PortalProfile` and `PortalShortcut`.
- **targeted Announcements Bulletin**: Publishes visibility-targeted bulletins and mailbox notices using `PortalAnnouncement` and `PortalNotification`.
- **Device Login Session Logs**: Monitors device fingerprint sessions logs using `PortalSession` and `PortalActivity`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIPortalAssistant`, `IAINotificationClassifier`, `IAIShortcutAdvisor`) are registered in the DI container.

## 31. Enterprise School Administration & Super Admin Control Center (ESSACC) Lock
- **SaaS Configurations & Subscriptions**: Mapped pricing packages, subscriber renew cycles, and feature licensing slots using `PlatformSetting`, `SubscriptionPlan`, `SchoolSubscription`, and `ModuleLicense`.
- **White-Labeling & Flags**: Overrides school stylesheets and domains configurations using `SchoolSetting`, `SchoolBranding`, and `FeatureFlag`.
- **Developer Keys & Audits**: rotation tokens key strings and global audits are cached in `APIKey` and `PlatformAudit`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAISubscriptionAdvisor`, `IAILicenseOptimizer`, `IAIBrandingCoach`, `IAIAuditInspector`) are registered in the DI container.

## 32. Enterprise AI Platform & Automation Engine (EAPAE) Lock
- **Multi-Model Provider Routing**: Routes prompt messages to fallback providers dynamically using `AIProvider`, `AIModel`, and `AIConversation`.
- **Reusable prompt Versioning**: Caches system instructions revisions versions in `PromptTemplate` and `PromptVersion`.
- **Semantic RAG Ingestion**: Stores split text knowledge snippets in `KnowledgeDocument` and `KnowledgeChunk`.
- **Event-Driven Automations**: Triggers background tasks using `AutomationRule` and `AIEmbedding`.
- **Pluggable AI Provider Extensions**: Abstract stubs (`IAIProvider`, `IAIEmbeddingProvider`, `IAIChatProvider`, `IAIAutomationProvider`) are registered in the DI container.

## 33. Enterprise Flutter Mobile Platform (EMFP) Lock
- **Clean Architecture Hierarchy**: Enforces isolation across presentation, domain, and data layers within 21 feature modules.
- **Offline Sync Engine**: Queues background operations via Hive caching and Drift persistent stores.
- **Universal Design Tokens**: Locks semantic components, typography scaling, and brand colors within `eduorbit_design_system`.
- **Role-Based Execution Contexts**: Routes traffic via declarative GoRouter configurations across 6 discrete role shells.
- **Hardened Mobile Perimeters**: Enforces token cryptography, JWT refresh routines, root detections, and SSL certificate pinning.

## 34. Enterprise UI/UX Completion Lock
- **Tailwind CSS v3.4 Pipeline**: Freezes the utility-first CSS architecture, configuring purging rules for all Django templates, HTMX fragments, and Alpine.js directives.
- **Material Design 3 Component Library**: Locks the reusable template components (buttons, cards, inputs, modals, tables) ensuring consistency across all 13 primary dashboards.
- **Role-Based HTMX Dashboards**: Defines the standard command center layouts for Super Admin, School Admin, Teacher, Student, Parent, Finance, HR, Library, Clinic, Transport, Hostel, Inventory, and Analytics roles.
- **Centralized Base Templates**: Fixes the structural layouts (`_document.html`, `_sidebar.html`, `_topbar.html`) and the dark mode theme engine configurations.

## 35. Enterprise Production Infrastructure & DevOps (EPID) Lock
- **Native Ubuntu Stack**: Freezes the production environment on Ubuntu 24.04 LTS natively using Nginx, Gunicorn, PostgreSQL, and Redis (explicitly excluding Docker/Kubernetes).
- **Service Orchestration**: Locks the systemd unit files (`gunicorn.service`, `celery.service`, `celerybeat.service`, `flower.service`) ensuring reliable auto-restarts and background execution.
- **Continuous Integration / Continuous Deployment (CI/CD)**: Establishes a zero-downtime automated pipeline via GitHub Actions bridging from unit tests directly to SSH droplet deployment.
- **Multi-Tenant Provisioning Engine**: Implements the automated scripts (`create_school.sh`, `provision_tenant.py`) linking PostgreSQL schema creation to custom Nginx domain generation.
- **Disaster Recovery Protocols**: Freezes the daily automated `pg_dump` and media archiving pipelines pushing immutable backups directly to DigitalOcean Spaces with automated verification steps.

## 36. Enterprise Certification, QA & Version 1.0 Release (ECR) Lock
- **Demo Seed Engine**: Freezes the `seed_all` management commands and faker factories generating 600+ users, 13 staff roles, and massive relational datasets spanning all 28 modules.
- **Automated Certification Suites**: Locks the End-to-End (`LiveServerTestCase`), Performance (`Locust`), and Security testing modules ensuring platform stability.
- **Gold Release Tagging**: Certifies EduOrbit as Version 1.0.0, finalizing the `CHANGELOG.md`, `RELEASE_NOTES.md`, and locking the core architecture from further feature additions.
