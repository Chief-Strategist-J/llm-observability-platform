# Data Normalization & Denormalization Policy Reference
*(Senior / Architect-Level Reference for Relational Normalization 1NF-3NF/BCNF, Strict Anti-Pattern Bans, Denormalization RFC Controls, and Data Integrity)*

---

## 1. Relational Normalization Standards (1NF to 3NF/BCNF)

All relational OLTP databases (PostgreSQL) MUST adhere to **3rd Normal Form (3NF)** by default during initial schema design.

```
┌─────────────────────────────────────────────────────────────┐
│ 1NF: Atomic values, no array lists in relational columns    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2NF: No partial dependencies (all attributes depend on PK)   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3NF: No transitive dependencies (attribute -> attribute)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ BCNF: Every determinant is a candidate key                  │
└─────────────────────────────────────────────────────────────┘
```

- **1NF (First Normal Form)**: Every column contains atomic (indivisible) values. Repeating groups or comma-separated strings inside a single text field are strictly prohibited.
- **2NF (Second Normal Form)**: Table is in 1NF and all non-key attributes are fully dependent on the entire primary key (no partial key dependencies).
- **3NF (Third Normal Form)**: Table is in 2NF and no non-key attribute depends on another non-key attribute (no transitive dependencies).
- **BCNF (Boyce-Codd Normal Form)**: Every determinant in the table is a candidate key.

---

## 2. Non-Negotiable Normalization Rules & Anti-Pattern Bans

| Rule # | Restriction / Requirement | Reason / Risk | Enforcement |
|---|---|---|---|
| **RULE-01** | **No Relational Data in JSONB**: Foreign keys and relational entities MUST NOT be hidden inside `JSONB` blobs. `JSONB` is permitted ONLY for schema-less, arbitrary payload data (e.g. raw LLM call parameters). | Prevents unindexed queries, broken referential integrity, and data corruption. | Linter & PR Review |
| **RULE-02** | **Mandatory Foreign Key Constraints**: Every relational table relationship MUST declare an explicit `FOREIGN KEY` constraint and have an index on the foreign key column. | Un-constrained foreign key strings lead to orphan rows and deletion anomalies. | Migration CI Check |
| **RULE-03** | **Enums as `VARCHAR` + `CHECK`**: Enums MUST be stored as `VARCHAR` with a `CHECK` constraint. Postgres native `CREATE TYPE ... AS ENUM` is strictly forbidden. | Native DB enums require exclusive table locks during modifications and complicate migrations. | Migration Linter |
| **RULE-04** | **Mandatory Identity & Audit Columns**: Every normalized table MUST include `id` (PK), `created_at` (TIMESTAMPTZ), `updated_at` (TIMESTAMPTZ), and `deleted_at` (TIMESTAMPTZ, nullable for soft deletes). | Enables auditability, event sourcing, and soft-delete recovery. | Schema Validation CI |
| **RULE-05** | **No Comma-Separated Lists or Arrays**: Storing lists (`"1,2,3"`) or native array columns to simulate 1:N relations is prohibited. Use a dedicated Junction/Bridge table for M:N relationships. | Violates 1NF; breaks relational indexing and join efficiency. | Code Review |
| **RULE-06** | **Explicit ON DELETE Behavior**: Every foreign key constraint MUST explicitly declare `ON DELETE RESTRICT` or `ON DELETE CASCADE`. Implicit default deletion behavior is banned. | Prevents silent data deletion anomalies or unintended cascading purges. | Schema Linter |

---

## 3. Strict Denormalization Approval Process & RFC Thresholds

Denormalization introduces data redundancy and risk of update anomalies. Denormalization is **strictly prohibited** unless all of the following conditions are satisfied:

### A. Denormalization RFC & Benchmark Evidence
To introduce a denormalized field or summary table, a developer MUST submit a Denormalization RFC including:
1. **Empirical Query Benchmark**: An `EXPLAIN ANALYZE` execution trace proving that the normalized 3NF join across 4+ tables exceeds the latency SLA ($p95 > 100\text{ms}$) under production data volume ($\ge 100,000$ rows).
2. **Access Pattern Justification**: Proof that the read-to-write ratio for the target entity exceeds $100:1$.

### B. Approved Denormalization Use Cases
1. **High-Read Join Bottlenecks**: Derived views where normalized join cost violates production latency SLAs under high concurrency.
2. **Pre-Aggregated Summary Counters**: Storing aggregate counters (`order_count`, `total_spend_cents`) on parent records to eliminate expensive runtime `COUNT(*)` or `SUM()` table scans.
3. **Historical Point-in-Time Snapshots**: Copying address, pricing, or tax rates into an invoice/order record at the moment of transaction creation (so subsequent customer profile updates do not corrupt historical financial records).

---

## 4. Denormalization Governance & Data Integrity Controls

When denormalization is approved, the following 4 architectural controls are **MANDATORY**:

```
┌─────────────────────────┐          Sync / CDC Worker          ┌─────────────────────────┐
│ Primary Normalized SSOT ├────────────────────────────────────►│ Denormalized Read View  │
│ (Single Source of Truth)│                                     │ (Pre-aggregated Table)  │
└────────────┬────────────┘                                     └────────────▲────────────┘
             │                                                               │
             └────────────────── Scheduled Reconciler Job ──────────────────┘
```

1. **Single Source of Truth (SSOT)**:
   - Normalized tables remain the canonical Single Source of Truth.
   - Denormalized tables or columns are treated as **read projections** derived strictly from the SSOT.
2. **Zero Dual-Write in Application Code**:
   - Application code MUST NEVER attempt manual dual-writes to both normalized and denormalized tables in separate un-transactional queries.
   - Synchronization MUST be handled via **Database Triggers**, **Transactional Outbox Pattern**, or **Change Data Capture (CDC via Debezium)**.
3. **Data Drift Reconciler Job**:
   - A scheduled background job MUST run periodically (nightly) to compare normalized source data with denormalized projections, log all diffs, and automatically repair data drift.
4. **Drift SLA & Alerting**:
   - Data drift count MUST NOT exceed **0.001%** of total row count.
   - Reconciler jobs MUST export `database_data_drift_count` Prometheus metrics and trigger high-priority alerts if drift exceeds zero.
