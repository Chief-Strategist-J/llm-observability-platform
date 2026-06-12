Feature Migration Strategy — Aggregating Migrations
Each feature owns its migrations inside its own folder. The database/migrations/ directory at the package root is the aggregated, ordered set that the migrate.sh script runs. Migrations are numbered sequentially across all features.

Migration ownership and aggregation
│
├── src/features/payments/migrations/
│   ├── 0001_payments_init.sql          ← owned by payments feature
│   └── 0001_payments_init.rollback.sql
│
├── src/features/refunds/migrations/
│   ├── 0002_refunds_init.sql           ← owned by refunds feature
│   └── 0002_refunds_init.rollback.sql
│
└── database/migrations/                ← aggregated by a generate step or symlinks
    ├── 0001_payments_init.sql          ← copied or linked from feature
    ├── 0001_payments_init.rollback.sql
    ├── 0002_refunds_init.sql
    └── 0002_refunds_init.rollback.sql

Each feature authors and owns its migration files.
The aggregated database/migrations/ is the single directory migrate.sh reads.
Migration numbers are globally sequential across all features — no two features use the same number.
A feature's migration is merged before the feature code that depends on the new schema.
