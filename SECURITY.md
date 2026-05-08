# Security Policy

## Supported Versions

Only the latest `main` branch is supported for security fixes.

| Version | Supported |
| ------- | --------- |
| `main`  | Yes |
| All other branches, tags, and releases | No |

Security issues in unsupported versions will not be patched.

---

## Reporting a Vulnerability

Security vulnerabilities must be reported privately.

### Do Not
- Open a public issue
- Post details in discussions, pull requests, or comments
- Share exploit steps, screenshots, logs, or proof-of-concept code publicly
- Attempt active exploitation beyond minimal validation needed to confirm the issue

### Do
- Report the issue through a private security channel
- Include only the minimum technical detail needed to reproduce the problem
- Wait for acknowledgment before any disclosure
- Keep all communication confidential

---

## Required Report Content

Provide, at minimum:

- A clear description of the vulnerability
- Affected component(s)
- Steps to reproduce
- Expected versus actual behavior
- Potential impact
- Any relevant logs or proof-of-concept material, shared privately only

Reports missing essential details may be closed until complete information is provided.

---

## Response Process

1. The report is received and reviewed privately.
2. The vulnerability is triaged and validated.
3. A fix is developed and tested.
4. A patch is released before public disclosure when possible.
5. Disclosure occurs only after mitigation is available, unless legal or operational constraints require otherwise.

We do not provide timelines, status guarantees, or progress updates beyond what is necessary for safe coordination.

---

## Scope

This policy applies to all repository-controlled assets, including:

- Application code
- Streamlit UI components
- API and integration logic
- Infrastructure and orchestration scripts
- Docker and container configurations
- Deployment files
- Telemetry, tracing, and observability pipelines
- Authentication, authorization, and credential-handling code
- Configuration and environment management

---

## Prohibited Behavior

Contributors must not:

- Add hardcoded secrets, keys, tokens, passwords, or credentials
- Commit `.env` files or similar secret-bearing files
- Disable security checks without justification
- Bypass authentication, authorization, or rate limits
- Introduce insecure defaults
- Expose internal services, databases, or admin endpoints publicly
- Embed unreviewed third-party code that processes sensitive data

Any change that weakens security controls may be rejected.

---

## Dependency and Supply Chain Security

All dependency changes must be reviewed with security in mind.

- Use only necessary packages
- Prefer well-maintained dependencies
- Review transitive dependency impact
- Verify package provenance when applicable
- Reject dependencies with unresolved critical vulnerabilities when a safer alternative exists

---

## Infrastructure Security

Infrastructure changes must follow least-privilege and secure-by-default principles.

- Do not expose services unnecessarily
- Use private networking where possible
- Restrict credentials and permissions
- Validate container and orchestration settings
- Avoid elevated privileges unless strictly required and clearly justified

---

## Disclosure Rules

By reporting a vulnerability, you agree to:

- Keep the issue confidential until authorized disclosure
- Avoid public mention of the vulnerability
- Refrain from exploiting the issue in production or shared environments
- Cooperate with the maintainers during remediation

Violation of these rules may result in the report being closed without further response.

---

## Safe Handling of Sensitive Data

Never include real secrets in:

- Issues
- Pull requests
- Commit messages
- Screenshots
- Logs
- Documentation examples

Use placeholder values only.

---

## Acknowledgment

Responsible security reporting is appreciated. Clear, private, and minimal disclosure is required.
