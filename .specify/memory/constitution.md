<!--
SYNC IMPACT REPORT
==================
Version change: (unversioned template) → 1.0.0
Initial ratification — all placeholders replaced.

Modified principles: N/A (initial authoring)

Added sections:
  - Core Principles (I–V)
  - Security & Data Privacy
  - Development Quality Gates
  - Governance

Removed sections: N/A

Templates reviewed:
  ✅ .specify/templates/plan-template.md
     — Constitution Check section dynamically references this file; no edits needed.
     — "Tests are OPTIONAL" note in tasks-template is superseded by Principle IV for this project.
  ✅ .specify/templates/spec-template.md
     — No constitution-driven mandatory section changes required.
  ✅ .specify/templates/tasks-template.md
     — Per Principle IV, test tasks are MANDATORY for this project even though the
       template marks them optional by default. Planners must treat the template's
       ⚠ "OPTIONAL" note as overridden.
  ⚠ .specify/templates/commands/ — no commands directory found; skip silently.

Deferred TODOs: None.
-->

# InBody Scan Analyzer Constitution

## Core Principles

### I. Extensibility by Design (NON-NEGOTIABLE)

Every module, service, and UI component MUST be designed with clear extension points
so that new features can be added without modifying stable, existing interfaces.

- Public interfaces MUST be separated from implementation. Internal implementation
  details MUST NOT be depended upon by other modules.
- New capabilities MUST be addable by extending or composing existing units, not by
  editing their internals (Open/Closed Principle).
- Data models and API contracts MUST be versioned or designed to accommodate additive
  changes (new fields, new endpoints) without breaking existing consumers.
- Shared services (authentication, recommendation engine, scan parser) MUST expose
  well-defined interfaces so they can be swapped or upgraded independently.

**Rationale**: The application is explicitly scoped as v1 of a growing product.
Architectural shortcuts taken now will become blockers when the next feature is added.
Extensibility is cheaper to build in at the start than to retrofit later.

### II. Algorithm Efficiency

All algorithms MUST be chosen and implemented with appropriate time and space
complexity for their context.

- Any operation with O(n²) or worse complexity MUST be documented with explicit
  justification explaining why a more efficient alternative is not feasible.
- Performance-sensitive paths — PDF metric extraction, scan comparison deltas,
  chart data aggregation, LLM prompt construction — MUST be profiled before
  the feature is marked complete.
- Database queries MUST use indexed lookups for all user-scoped data access patterns.
  Full-table scans on health data tables are prohibited without justification.
- Pagination or lazy loading MUST be applied wherever datasets can grow
  unboundedly (scan history, recommendation history).

**Rationale**: Health data accumulates over time. An inefficient query or
aggregation that is acceptable with 5 scans becomes a user-visible problem
with 50. Efficiency must be a first-class concern, not a retrofit.

### III. License Compliance (NON-NEGOTIABLE)

Only software distributed under permissive, non-copyleft licenses may be used
as a dependency or embedded in this project.

- **Permitted**: MIT, Apache 2.0, BSD (2-clause and 3-clause), ISC, CC0,
  Unlicense, and equivalent permissive licenses.
- **Prohibited without legal review**: GPL (any version), AGPL, LGPL, EUPL,
  CDDL, MPL, and any proprietary or source-available license.
- All new dependencies MUST have their license verified before being added
  to the project. A comment or entry in the dependency manifest MUST note
  the confirmed license.
- Transitive dependencies (dependencies of dependencies) MUST also be checked.
  A dependency that pulls in an AGPL transitive dependency is itself prohibited.
- Data sources (e.g., USDA FoodData Central) MUST have usage rights confirmed
  for the intended use case (public API, bulk download, embedded dataset).

**Rationale**: The application may be commercialized or deployed to clients.
Copyleft licenses can impose obligations that conflict with commercial or
proprietary deployment. Prevention is the only viable strategy.

### IV. Mandatory Test Coverage (NON-NEGOTIABLE)

Every unit of functionality MUST have corresponding, passing test cases before
it is considered complete. Tests are not optional for this project.

- **Unit tests** MUST cover all business logic functions, data transformations,
  and validation rules.
- **Integration tests** MUST cover all API endpoints, database access patterns,
  PDF extraction flows, and LLM recommendation generation flows.
- **End-to-end tests** MUST cover each P1 and P2 user story's primary acceptance
  scenario as defined in the feature specification.
- Tests MUST be written before or alongside implementation — never deferred to
  a later phase.
- A feature branch MUST NOT be merged if any test is failing or if new
  functionality lacks test coverage.
- The tasks template's "Tests are OPTIONAL" note does NOT apply to this project.
  All task lists generated for this codebase MUST include test tasks.

**Rationale**: Health and dietary data is sensitive. Bugs in recommendation
logic, data isolation, or scan parsing can directly harm users. Comprehensive
tests are the primary defence against regressions as the feature set grows.

### V. UI/UX Consistency

All user-facing interfaces MUST adhere to a single, shared design system.
Visual inconsistency across screens is a defect, not a style preference.

- A design token set (colors, typography scale, spacing scale, border radii,
  shadow levels) MUST be defined and used project-wide. Ad-hoc inline values
  that duplicate or deviate from tokens are prohibited.
- A shared component library (buttons, inputs, cards, charts, modals, navigation)
  MUST be the sole source of UI primitives. Reimplementing a component that
  already exists in the library is prohibited.
- Every new screen or feature MUST be reviewed against the existing design system
  before implementation is accepted.
- Dark mode, accessibility contrast ratios (WCAG AA minimum), and responsive
  breakpoints MUST be applied uniformly across all screens using the design system.
- Chart types, color palettes for data visualization, and labeling conventions
  MUST follow a single charting style guide defined during the planning phase.

**Rationale**: The application spans many screens (dashboard, metrics, profile,
admin portal, recommendations). Without a shared design system, visual drift
accumulates quickly and erodes user trust in a health-focused product where
professionalism is critical.

## Security & Data Privacy

This application processes sensitive personal health data. The following rules
are non-negotiable.

- All data transmitted between client and server MUST use encrypted transport
  (TLS 1.2 minimum).
- All health data stored at rest (scan metrics, recommendations, profile data)
  MUST be encrypted.
- Every data access operation MUST enforce user-scoped authorization. Queries
  MUST include the authenticated user's identifier as a filter — never retrieve
  all records and filter in application code.
- Passwords MUST be stored as salted hashes using a current, recommended
  algorithm. Plaintext or reversibly-encoded password storage is prohibited.
- Admin accounts MUST NOT have read access to individual user health records.
  The admin role is scoped to account management only.
- No health data, personally identifiable information, or credentials MUST be
  logged in plain text in application logs.
- LLM prompts sent to external AI providers MUST NOT include raw personally
  identifiable information. Data sent to the LLM MUST be anonymized or
  de-identified at the service boundary.

## Development Quality Gates

The following gates MUST be satisfied before any feature branch is merged.

- All tests (unit, integration, end-to-end) MUST pass with no failures.
- No new dependency may be introduced without a confirmed-permissive license entry.
- No new UI screen or component may ship without design-system token usage verified.
- All O(n²) or worse algorithmic choices MUST have documented justification in
  the implementation plan or as a code comment at the algorithm site.
- Data access code MUST be reviewed to confirm user-scoped filtering is applied.
- LLM prompt templates MUST be reviewed to confirm no PII is transmitted.

## Governance

This constitution supersedes all other development practices and conventions for
this project. In cases of conflict, the constitution takes precedence.

- **Amendments**: Any change to this constitution requires updating this file,
  incrementing the version per semantic versioning rules, and updating the
  Sync Impact Report header comment.
- **Version policy**: MAJOR for principle removals or backward-incompatible
  redefinitions; MINOR for new principles or materially expanded guidance;
  PATCH for clarifications, wording, and non-semantic refinements.
- **Compliance review**: Each implementation plan (plan.md) MUST include a
  "Constitution Check" section that maps each principle to concrete gates
  for that feature.
- **Override policy**: No principle may be bypassed without an explicit entry
  in the feature plan's Complexity Tracking table, stating the reason and
  the simpler alternative that was considered and rejected.

**Version**: 1.0.0 | **Ratified**: 2026-03-31 | **Last Amended**: 2026-03-31
