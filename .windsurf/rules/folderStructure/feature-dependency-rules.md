Feature Dependency Rules
A feature's service may call another feature only via that feature's index — never via its service, repository, or any internal file.
A feature's handler calls only this feature's index — never another feature's index directly.
A feature's repository calls only infra adapters via the port interface — never another feature's repository.
A feature never imports from the handler, api, or infra layers above it.
Features at the same level are peers. They communicate through their indexes, not by reaching into each other.
If two features need to share a type, the shared type is promoted to the package's shared/types/ — never duplicated.

Feature vs Package — When to Promote
A feature stays inside a package as long as it is only consumed internally. It becomes its own package when an external consumer needs it or when it grows beyond a manageable size.

Signal
Action
Feature is called only inside this package
Keep it as a feature inside the package
Feature is called by another package
Promote: write a shared contract, expose via API, create generated client
Feature has more than 5 sub-concerns that are growing independently
Split into sub-features or promote to its own package
Feature has its own independent deployment cadence
Promote to its own package
Feature needs to scale independently from the rest of the package
Promote to its own package
Two features share more than 3 types
Extract shared types to package shared/types/

