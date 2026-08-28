# Independent Audit & Remediation Registry (`llm-obs-infra/audits`)

| Field | Value |
|---|---|
| Registry Location | `packages/configs/llm-obs-infra/docs/securityDoc/audits/` |
| Scope | Independent Architecture, Security, Performance & Compliance Audits |
| Status | Active Registry |

---

## Overview

This registry serves as the master catalog for all independent security, architecture, performance, and compliance audit reports for the `llm-obs-infra` platform.

Each audit report is stored in its own dedicated, version-controlled markdown document. Every audit is paired with an actionable, technical **Remediation Plan** that outlines concrete code changes, configuration patches, target files, and verification commands required for implementation.

---

## Audit Catalog

| Audit ID | Target Component / ADR | Severity Breakdown | Audit Report Link | Technical Remediation Plan Link | Status |
|---|---|---|---|---|---|
| AUD-0006 | ADR-0006 Resilience & Hardening | 3 Critical, 4 High, 6 Medium, 4 Low | [independent-audit-adr-0006.md](./independent-audit-adr-0006.md) | [remediation-plan-adr-0006.md](./remediation-plan-adr-0006.md) | Open / In Remediation |

---

## Adding New Audits (Standard Operating Procedure)

When adding a new independent audit to this repository, follow these rules:

1. **Standalone File**: Create a dedicated document named `independent-audit-<topic-or-adr>.md` inside `docs/securityDoc/audits/`.
2. **Remediation Plan**: Create a corresponding implementation plan named `remediation-plan-<topic-or-adr>.md` containing finding IDs, code snippets, target files, and checkboxes.
3. **Registry Entry**: Add a row to the Audit Catalog table above in `docs/securityDoc/audits/README.md`.
4. **No Emojis**: Maintain plain-text markdown severity tags (`[Critical]`, `[High]`, `[Medium]`, `[Low]`, `Pass`, `Warning`, `Fail`).
5. **Cross-Linking**: Update the central [docs/README.md](../README.md) catalog index to reference the new audit.
