
Part B — Workflow Versioning & Migration Guide

Workflow Versioning Rule Zero
A deployed workflow definition must never be changed in a way that breaks replay of existing history. Any change that alters the command sequence a workflow produces is a breaking change and requires a versioning strategy before deployment.

What Is a Breaking Workflow Change

Breaking — versioning required
Compatible — safe to deploy
Adding a new activity call in an existing execution path
Adding a new signal handler
Removing an activity call
Adding a new query handler
Changing the order of activity calls
Adding a new workflow (does not affect existing)
Adding or removing a timer
Adding a new activity type that is only called in new code paths
Changing a signal name
Adding optional fields to activity output
Changing a query name
Bug fixes that do not alter the command sequence
Changing workflow input or output types non-additively
Adding logging or metrics calls
Adding or removing a child workflow call
Changing timeout values on new executions only


Workflow Versioning Strategy — Temporal GetVersion / Patching
Strategy 1 — Version Gate (for small, isolated changes)
Identify the exact point in the workflow where the logic changes.
Wrap the old and new logic in a version check using the SDK's GetVersion or patching API.
Deploy the new workflow definition. Existing open executions take the old path. New executions take the new path.
After all open executions using the old path have completed, remove the old code branch.
Deploy the cleaned-up workflow definition.
Add the old version to the deprecated-versions list in .package-meta.yaml.

Strategy 2 — New Workflow Type (for large changes)
Create a new workflow type with a new name in workflows/{new-workflow-name}/.
Publish the new interface in shared/workflows/{new-name}/v1.yaml.
Run old and new workflow types in parallel.
Migrate all new workflow starts to the new type.
After all open executions of the old type complete, deprecate the old type.
Remove the old type after the deprecation sunset period.

Replay Testing — Mandatory Before Any Workflow Change
Before deploying any workflow change, capture the history of at least one representative open execution.
Store the history as a JSON file in tests/replay/.
Run the replay test against the new workflow definition. The replay must complete without a non-determinism error.
Replay tests run on every PR that touches any workflow file. A replay failure blocks the PR. No exceptions.
History files in tests/replay/ are checked into the repository and are updated only when a new version gate is added.

Activity Interface Versioning
Adding optional fields to ActivityInput or ActivityOutput is compatible.
Removing fields from ActivityInput or ActivityOutput is a breaking change.
Changing the type of an existing field is a breaking change.
A breaking change to an activity interface requires a new activity type name.
Old activity type runs alongside new activity type until all open executions using it complete.

Job Schema Versioning — Queue Workers
Job payload schemas are versioned in contracts/jobs/{name}/v1.yaml.
Adding optional fields to a job payload is compatible.
Removing or renaming fields is a breaking change and requires a new schema version.
The producer and consumer must agree on the schema version via .contract-lock.
Old schema version jobs in the queue must be drained before the old consumer is removed.

Event Schema Versioning — Event Workers
Event schemas are versioned in shared/contracts/asyncapi/{event}/v1.yaml.
Adding optional fields is compatible.
Removing or renaming fields is a breaking change and requires a new schema version.
The consuming event worker pins the schema version in .contract-lock.
Both schema versions are consumed simultaneously during transition.

Worker Migration — Adding a New Worker
Write the worker contract first — workflow YAML, job YAML, schedule YAML, or event YAML.
Add the worker entry to shared/worker-registry.yaml.
Open a contract-only PR. No source files. Lint must pass. One review minimum.
Create the worker package folder structure for stage 0.
Implement workflows or job processors behind the contract.
Write unit tests and replay tests (Temporal only) alongside the implementation.
Write 0001_init.sql if the worker has its own database.
Add run.sh, migrate.sh, and test.sh as the minimum script set.
Promote to stage 1 in a dedicated promotion PR when production deploy is planned.

Worker Migration — Retiring a Worker
PR 1: Mark all workflow types or job types as deprecated in their contracts. Set a sunset date.
PR 2: Stop routing new executions to the deprecated worker. Old executions continue to completion.
PR 3: After all open executions complete and the sunset date passes, remove the worker package.
PR 4: Remove the worker entry from shared/worker-registry.yaml.
PR 5: Remove the worker's published contracts from shared/workflows/ or shared/jobs/.
Each PR is deployed to staging and verified before the next PR opens.

Worker Migration — Splitting a Worker
When a Temporal worker hosts too many unrelated workflows and needs to be split into two focused workers:
PR 1: Create the new worker package with its own task queue. Publish its contracts.
PR 2: Move the target workflows to the new worker. Register them on the new task queue.
PR 3: Run both old and new workers in parallel. New workflow starts go to the new task queue.
PR 4: After all open executions on the old task queue for the moved workflows complete, remove them from the old worker.
PR 5: Update worker-registry.yaml to reflect the final state.

Non-Negotiables for Worker Operations
Never deploy a workflow change without running replay tests first.
Never change a workflow definition in a way that breaks existing open executions.
Never share a task queue between two different workers.
Never call activity functions directly from workflow code — always use the SDK scheduling API.
Never put IO inside a workflow definition.
Never run a worker in production without tracing flowing to the collector.
Never retire a worker while it has open executions.
Never add a new worker without an entry in shared/worker-registry.yaml.
Never change a signal or query name without a deprecation period.
Never skip the contract PR when adding a new workflow, job type, or schedule.
