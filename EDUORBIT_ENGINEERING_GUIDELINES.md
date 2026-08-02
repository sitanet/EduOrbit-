# EduOrbit Engineering Rule – Simplicity First

You are developing EduOrbit, a School Management ERP. Follow these engineering principles for every task.

## 1. Core Principle

EduOrbit is not an enterprise framework like SAP, Oracle HCM, or Workday.
It is a practical, maintainable School Management ERP.
Always implement the smallest, cleanest, and most maintainable solution that satisfies the business requirement.

## 2. Before Writing Any Code

Before making any implementation, answer these questions internally:
- Can this be implemented by modifying existing code?
- Is this feature actually required for a school?
- Will this introduce unnecessary complexity?
- Can this be completed using the current architecture?
- Will this increase future maintenance without providing immediate business value?

If the answer is yes, modify the existing implementation. Do not create a new subsystem.

## 3. Repository Audit (Mandatory)

Before proposing any implementation:
- Audit the existing repository.
- Search for existing models, services, serializers, views, templates, utilities, and APIs that already solve part of the problem.
- Reuse existing code whenever possible.
- Never duplicate functionality.

If an existing component can be extended, extend it.

## 4. Do NOT Create Unless Explicitly Requested

Do not introduce any of the following unless explicitly requested:
- Generic engines
- Generic frameworks
- Generic media platforms
- Event buses
- Provider abstractions
- Plugin architectures
- AI pipelines
- Background workers
- Generic processing pipelines
- Processing telemetry
- Generic versioning systems
- Complex caching layers
- Domain-driven architecture
- CQRS/Event Sourcing
- Microservices
- Over-engineered abstractions

## 5. Architecture Rule

Prefer:
- Modifying existing models
- Extending existing services
- Extending existing views
- Extending existing serializers
- Extending existing templates
- Extending existing JavaScript

instead of introducing new frameworks.

If a feature belongs only to HR, keep it inside HR. Do not move it into Core unless explicitly requested as a reusable framework.

## 6. Scope Control

Implement only what was requested. Do not add:
- future enhancements
- optional enterprise features
- hypothetical scalability features
- "while we're here" improvements
- unrelated refactoring

Build exactly what is required today.

## 7. Existing Code Protection

Do not rename:
- Models
- Database fields
- APIs
- URLs
- Services
- Serializers
- Templates

unless absolutely necessary. Maintain backward compatibility and avoid breaking existing functionality.

## 8. Simplicity Rule

If a feature can be implemented by changing:
- one model
- one service
- one view
- one template

then do exactly that. Do not redesign the architecture.

## 9. Line Count Guideline

If the requested feature can reasonably be implemented in 300–800 lines, do not redesign it into a 3,000–10,000 line framework.
Keep the implementation proportional to the business requirement.

## 10. Priority Order

Always prioritize:
1. Complete business functionality
2. Stability
3. Simplicity
4. Maintainability
5. Code reuse
6. Performance
7. Future extensibility

Never sacrifice 1–5 for 6–7.

## 11. Required Response Format

Every implementation proposal must contain only:
- Repository Audit
- Files to Modify
- Why Each File Changes
- Implementation Plan
- Verification Plan

Do not include future roadmap items unless explicitly requested.

## 12. Definition of Done

A feature is complete when:
- The requested functionality works.
- Existing functionality is not broken.
- Code passes project checks and tests.
- The implementation follows the existing project architecture.
- No unnecessary files, frameworks, or abstractions were introduced.

Do not expand the implementation beyond the requested scope.
