# Data Normalization & Denormalization Policy Reference
*(Senior / Architect-Level Reference for Relational Normalization 1NF-3NF/BCNF, Pragmatic Denormalization Thresholds, and Data Reconciliation)*

---

### 1. Relational Normalization Standards (1NF to 3NF/BCNF)

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
```

- **1NF (First Normal Form)**: Every column contains atomic (indivisible) values. Repeating groups or comma-separated strings inside a single text field are strictly prohibited.
- **2NF (Second Normal Form)**: Table is in 1NF and all non-key attributes are fully dependent on the entire primary key (no partial key dependencies).
- **3NF (Third Normal Form)**: Table is in 2NF and no non-key attribute depends on another non-key attribute (no transitive dependencies).
- **BCNF (Boyce-Codd Normal Form)**: Every determinant in the table is a candidate key.

---

### 2. Pragmatic Denormalization Thresholds & Guidelines

Denormalization introduces data redundancy and risk of update anomalies. Denormalization is permitted ONLY when empirical benchmark data proves a performance necessity.

#### Approved Denormalization Criteria
1. **High-Read Join Bottlenecks**: Queries joining 4+ normalized tables where query execution time exceeds SLA threshold ($p95 > 100\text{ms}$) under production traffic load.
2. **Pre-Aggregated Summary Counters**: Storing aggregate metrics (`order_count`, `total_spend_cents`) on parent records to eliminate expensive runtime `COUNT(*)` or `SUM()` scans across millions of child rows.
3. **Historical Point-in-Time Snapshots**: Copying address, pricing, or tax rates into an invoice/order record at the time of creation (so subsequent updates to the customer's profile do not alter historical financial records).

---

### 3. Denormalization Governance & Data Integrity Controls

When denormalization is applied, the following 3 architectural controls are MANDATORY:

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
   - Denormalized tables or columns are treated as **read projections** derived from the SSOT.
2. **Atomic Synchronization Mechanism**:
   - Updates to denormalized projections MUST occur atomically using **Database Triggers**, **Transactional Outbox Pattern**, or **Change Data Capture (CDC via Debezium)**.
3. **Data Drift Reconciler**:
   - A scheduled background reconciliation job MUST run periodically (e.g. nightly) to compare normalized source data with denormalized projections, log any diffs, and automatically repair data drift.
