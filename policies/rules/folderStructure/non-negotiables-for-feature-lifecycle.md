Non-Negotiables for Feature Lifecycle

Never modify a feature's public contract without creating a new version.
Never remove a feature without going through the safe removal sequence.
Never add a feature flag without a cleanup_by date.
Never leave a deprecated feature running past its sunset date without an explicit extension decision.
Never ship a feature without tracing in the same PR.
Never delete a feature directory without a DROP TABLE migration for any tables it owned.
Never let a feature call another feature's internal files — only through the index.
Never let a feature's tests depend on another feature's test fixtures — each feature owns its data.
