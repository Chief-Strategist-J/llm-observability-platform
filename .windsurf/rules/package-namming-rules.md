# Package Naming Rules

1. MUST use lowercase only
2. MUST follow ecosystem-native separator style
3. MUST use ASCII characters only
4. MUST start with a letter
5. MUST NOT contain spaces
6. MUST NOT mix separators (`_`, `-`, `.`)
7. MUST use descriptive functional words
8. MUST place primary domain keyword first
9. MUST keep naming grammar consistent
10. MUST use one terminology consistently
11. MUST keep names human-readable
12. MUST keep names searchable
13. MUST keep names easily typable
14. MUST keep names pronounceable
15. MUST avoid abbreviations unless industry-standard
16. MUST avoid unnecessary acronyms
17. MUST avoid ambiguous wording
18. MUST avoid filler words (`utils`, `helper`, `common`)
19. MUST avoid marketing words (`ultra`, `smart`, `next`)
20. MUST avoid random suffixes (`x`, `plus`, `pro`)
21. MUST avoid unnecessary prefixes
22. MUST avoid version numbers in package names
23. MUST avoid trademark conflicts
24. MUST avoid collisions with existing popular packages
25. MUST align package name with actual scope
26. MUST keep naming scalable for ecosystems
27. MUST maintain deterministic naming structure
28. MUST maintain stable namespace hierarchy
29. MUST use consistent singular/plural strategy
30. MUST optimize for registry search discoverability
31. MUST optimize for autocomplete readability
32. MUST align package/repo/import names
33. MUST avoid misleading capability claims
34. MUST avoid unnecessary shortening
35. MUST avoid invented spellings unless brand-rooted
36. MUST separate brand and feature clearly
37. MUST keep names concise
38. MUST avoid sentence-like names
39. MUST avoid context-dependent names
40. MUST preserve consistency across all packages
41. MUST use same word ordering everywhere
42. MUST make purpose inferable immediately
43. MUST remain stable after public release

---

# Tag Rules

1. MUST use lowercase only
2. MUST be short and searchable
3. MUST represent actual functionality
4. MUST use singular canonical forms
5. MUST avoid vague tags (`tool`, `misc`, `general`)
6. MUST avoid marketing tags (`best`, `fastest`)
7. MUST group tags by domain/function/platform
8. MUST keep consistent terminology across ecosystem
9. MUST avoid duplicate semantic tags
10. MUST use stable tag vocabulary
11. MUST prioritize discoverability keywords
12. MUST avoid irrelevant trending keywords
13. MUST avoid excessive tags
14. MUST use ecosystem-recognized terminology
15. MUST align tags with package scope
16. MUST avoid internal/company-only jargon
17. MUST maintain deterministic tag structure
18. MUST avoid category overlap ambiguity
19. MUST keep tags machine-readable
20. MUST keep tags human-understandable

---

# Docker / Microservice Naming Rules

1. MUST use lowercase only
2. MUST use kebab-case for service names
3. MUST use stable service prefixes
4. MUST use consistent domain naming
5. MUST separate bounded contexts clearly
6. MUST name by business capability
7. MUST avoid infrastructure terminology in business services
8. MUST keep service names immutable after deployment
9. MUST align container, repo, and deployment names
10. MUST align image names with service names
11. MUST use deterministic naming hierarchy
12. MUST use environment-independent service names
13. MUST avoid host/location-specific naming
14. MUST avoid developer-specific naming
15. MUST avoid temporary/project-phase names
16. MUST avoid vague names (`service-api`, `backend-core`)
17. MUST make service purpose inferable immediately
18. MUST use clear API/domain ownership naming
19. MUST use consistent suffix strategy (`-api`, `-worker`, `-gateway`)
20. MUST use stable registry namespaces
21. MUST version Docker images using tags, not names
22. MUST use semantic version tags where applicable
23. MUST separate latest/stable/canary tags clearly
24. MUST avoid mutable production tags when possible
25. MUST keep image tags deterministic
26. MUST keep deployment names predictable
27. MUST keep Kubernetes resource naming aligned
28. MUST avoid overloaded “shared” services
29. MUST maintain naming consistency across environments
30. MUST optimize names for observability/logging/search systems

# Versioning Rules

1. MUST follow Semantic Versioning (`MAJOR.MINOR.PATCH`)
2. MUST increment MAJOR for breaking changes
3. MUST increment MINOR for backward-compatible features
4. MUST increment PATCH for backward-compatible fixes
5. MUST start stable public releases at `1.0.0`
6. MUST keep version format deterministic
7. MUST NOT skip version numbers arbitrarily
8. MUST NOT reuse published versions
9. MUST NOT modify artifacts after release
10. MUST tag releases consistently across repos/packages/images
11. MUST align git tags with published versions
12. MUST keep changelog aligned with versions
13. MUST document breaking changes explicitly
14. MUST use pre-release identifiers consistently
15. MUST use standard pre-release labels (`alpha`, `beta`, `rc`)
16. MUST use ordered pre-release progression (`alpha` → `beta` → `rc`)
17. MUST avoid custom/random pre-release labels
18. MUST keep pre-release numbering deterministic
19. MUST separate build metadata from semantic version
20. MUST avoid embedding environment names in versions
21. MUST avoid date-based versioning unless standardized project-wide
22. MUST keep API versioning strategy consistent
23. MUST version Docker images independently from deployment environments
24. MUST tag Docker images with immutable versions
25. MUST avoid relying only on `latest` tags
26. MUST maintain stable tags separately (`stable`, `lts`)
27. MUST keep rollback-compatible image history
28. MUST align microservice contract versions explicitly
29. MUST increment versions on schema/protocol changes
30. MUST avoid silent breaking changes
31. MUST use dependency version ranges intentionally
32. MUST pin critical production dependencies deterministically
33. MUST maintain backward compatibility guarantees clearly
34. MUST avoid incompatible changes in patch releases
35. MUST avoid feature additions in patch releases
36. MUST keep release cadence predictable
37. MUST archive deprecated versions cleanly
38. MUST define version support policy explicitly
39. MUST use immutable release artifacts
40. MUST ensure reproducible builds for same version
41. MUST validate upgrade paths between versions
42. MUST maintain migration documentation for major releases
43. MUST use consistent tagging across CI/CD pipelines
44. MUST keep registry versions synchronized with source control
45. MUST avoid overlapping release channels
46. MUST define EOL policy for unsupported versions
47. MUST maintain compatibility matrices where required
48. MUST keep client/server protocol versions traceable
49. MUST make version intent inferable immediately
50. MUST treat released versions as permanent public contracts
