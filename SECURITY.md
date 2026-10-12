# Security Policy

## Scope
RANIT is an early-stage DevOps CLI. Current commands inspect project metadata and local tool availability. AI repairs, arbitrary command execution, cloud provisioning, and deployment are not yet implemented.

## Reporting a vulnerability
Do not publish secrets, access tokens, cloud credentials, private keys, or exploit details in public issues. Contact the repository owner privately through GitHub security reporting options if available.

## Safe usage
- Only inspect projects you own or are authorized to work on.
- Treat unknown repositories and build scripts as untrusted.
- Do not run unknown scripts as Administrator/root.
- Never commit `.env` files, AWS keys, tokens, certificates, or private keys.
- Use least-privilege and short-lived AWS credentials for future cloud integrations.
- Require a plan and explicit approval before destructive or production infrastructure changes.
- Cloud resources may incur charges; budget alerts are not always hard spending limits.

## Current limitations
The initial analyzer reads filenames and directory metadata only. It does not sandbox or execute project code.
