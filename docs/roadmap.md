# RANIT Development Roadmap

This roadmap distinguishes existing code from planned capabilities.

## Phase 1 — CLI foundation
- [x] Python package and command entry point
- [x] Environment diagnostics
- [x] Read-only project marker scan
- [x] JSON output
- [x] Unit tests and GitHub Actions
- [x] Logo and repository documentation

## Phase 2 — Safe local automation
- [ ] Project-specific command plans
- [ ] Explicit dry-run mode
- [ ] Command allowlists, timeouts, and output redaction
- [ ] Python, Node.js, Java and Go build/test adapters
- [ ] Clear approval prompts before modifying files or installing packages

## Phase 3 — AI assistance
- [ ] Provider interface and configurable model backend
- [ ] Optional local model support
- [ ] Error summarization and proposed patches
- [ ] Diff preview and user approval before applying AI changes
- [ ] Retry limits and regression tests

## Phase 4 — Containers and CI/CD
- [ ] Dockerfile and Compose analysis/generation
- [ ] Image build and vulnerability scan integration
- [ ] CI workflow generation for GitHub Actions/Jenkins
- [ ] Test and health-check reporting

## Phase 5 — Infrastructure and deployment
- [ ] Terraform plan generation and plan review
- [ ] AWS identity/region preflight
- [ ] Least-privilege access validation
- [ ] Cost estimation warnings and resource allowlists
- [ ] Kubernetes context/namespace checks
- [ ] Explicit approval before resource creation/deletion
- [ ] Post-deploy health checks and guarded rollback

## Release readiness
- [ ] Cross-platform test matrix
- [ ] Dependency/security scanning
- [ ] Versioned releases
- [ ] Package publishing and installation guide
- [ ] User documentation and examples

No roadmap item should be described as implemented until code and tests exist.
