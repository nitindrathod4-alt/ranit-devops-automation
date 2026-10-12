# RANIT Architecture

## Current implementation

```text
User-selected local project
          |
          v
       RANIT CLI
          |
     +----+-----+
     |          |
  doctor     analyze
     |          |
Tool lookup  Read-only marker scan
     |          |
     +----+-----+
          |
   Human-readable / JSON output
```

The analyzer does not run project code, install packages, edit files, or create cloud resources.

## Intended architecture

1. **CLI** — accepts the user's local project path and requested task.
2. **Project inspector** — detects languages, package managers, tests, containers and infrastructure-as-code files.
3. **Planner** — proposes steps and explains expected changes.
4. **Policy/approval layer** — validates commands, target environment, cost boundaries and destructive actions.
5. **Execution adapters** — build/test, Docker, Terraform, AWS, Kubernetes and CI/CD.
6. **Verification** — checks exit codes, tests, health endpoints and deployment state.
7. **Audit report** — records proposed actions and outcomes without leaking secrets.

## Safety boundaries
- Do not assume repository code is trusted because it is local.
- Never store cloud credentials in project files or logs.
- Use dry-run and least privilege where possible.
- Require approval for production or destructive changes.
- Stop safely when required permissions, target details, or cost boundaries are missing.

This is the target architecture; not every component is implemented.
