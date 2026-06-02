Complete Runbook Folder Structure — All Types Together
==
Inside on each package (or under the root `notebooks/` directory for interactive/cross-package research)

runbooks/
│
├── registry.yaml                        ← index of every runbook across all categories
│
├── ansible/                             ← Category 1: Infrastructure Automation
│   ├── ansible.cfg
│   ├── requirements.yml
│   ├── inventory/
│   ├── group_vars/
│   ├── playbooks/
│   └── roles/
│
├── terraform/                           ← Category 1: Infrastructure Provisioning
│   ├── modules/
│   │   └── {module-name}/
│   └── environments/
│       ├── production/
│       ├── staging/
│       └── dev/
│
├── scripts/                             ← Category 5: Script / Code Runbooks
│   ├── services/
│   ├── workers/
│   └── platform/
│
├── notebooks/                           ← Category 3: Interactive Analysis
│   ├── investigations/
│   │   └── {YYYY-MM-DD}-{title}/
│   ├── analysis/
│   │   └── {service-or-worker}/
│   └── templates/
│
├── research/                            ← Category 4: Research & Spike
│   ├── {topic}/
│   │   └── {YYYY-MM-DD}-{study}/
│   │       ├── hypothesis.md
│   │       ├── research.ipynb
│   │       ├── findings.md
│   │       ├── data/
│   │       ├── outputs/
│   │       └── references/
│   └── templates/
│
├── api/                                 ← Category 6: API & Integration
│   ├── collections/
│   │   └── {service-name}/
│   │       └── {collection}.bru         ← Bruno format preferred (git-friendly)
│   └── environments/
│       ├── production.env
│       └── staging.env
│
├── helm/                                ← Category 7: Container & Orchestration
│   └── {service-or-worker}/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-staging.yaml
│       ├── values-production.yaml
│       └── templates/
│
├── observability/                       ← Category 9: Observability & Alerting
│   ├── dashboards/
│   │   └── {service-or-worker}.json
│   ├── alerts/
│   │   └── {service-or-worker}.yaml
│   └── queries/
│       ├── traceql/
│       └── logql/
│
├── security/                            ← Category 10: Security & Compliance
│   ├── vulnerability-response/
│   ├── secret-rotation/
│   └── access-review/
│
└── shared/                              ← Utilities shared across all runbook types
    ├── env/
    │   ├── .env.example
    │   └── validate-env.sh
    └── utils/

