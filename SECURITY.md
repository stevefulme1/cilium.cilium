# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in this collection, please report
it responsibly. **Do not open a public GitHub issue.**

### How to Report

1. Email the maintainers at **sfulmer@redhat.com** with:
   - A description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

2. You will receive an acknowledgment within **48 hours**.

3. We will work with you to understand the issue, develop a fix, and
   coordinate disclosure.

### What to Expect

- **Acknowledgment**: Within 48 hours of report.
- **Assessment**: Within 5 business days we will confirm the vulnerability
  and its severity.
- **Fix**: A patch will be developed and tested privately.
- **Disclosure**: A new release will be published with the fix, and a
  security advisory will be issued via GitHub.

## Security Best Practices for Users

When using this collection:

- **Never commit kubeconfig files** or service account tokens to version
  control.
- Use `no_log: true` on tasks that handle sensitive data such as secrets
  or certificates.
- Prefer **in-cluster** authentication when running on Kubernetes.
- Restrict RBAC permissions to the minimum required for Cilium management.
- Use Ansible Vault to encrypt sensitive variables in playbooks.
- Review Cilium network policies to ensure least-privilege access.
- Keep the `kubernetes` Python SDK updated to receive security patches.
