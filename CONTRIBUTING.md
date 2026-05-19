# Contributing to stevefulme1.cilium

Thank you for your interest in contributing to the Cilium Ansible
collection. This document explains the process for contributing code,
reporting issues, and running tests.

## Getting Started

### Prerequisites

| Requirement | Version |
|---|---|
| Python | >= 3.12 |
| ansible-core | >= 2.16 |
| kubernetes SDK | >= 28.1.0 |
| pytest | latest |

### Environment Setup

1. Fork the repository and clone your fork:

   ```bash
   mkdir -p ansible_collections/stevefulme1
   git clone https://github.com/<your-fork>/cilium.cilium.git \
     ansible_collections/stevefulme1/cilium
   cd ansible_collections/stevefulme1/cilium
   ```

2. Create a Python virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install ansible-core>=2.16 kubernetes grpcio \
     pytest pytest-cov yamllint flake8 ansible-lint
   ```

3. Configure Kubernetes credentials in `~/.kube/config` or via `KUBECONFIG`.

## Running Tests

### Linting

```bash
yamllint -c .yamllint .
flake8 plugins/ --max-line-length=120 --ignore=E402,W503
ansible-lint --strict
```

### Sanity Tests

```bash
ansible-test sanity --python 3.12 -v
```

### Unit Tests

```bash
pytest tests/unit/ -v --tb=short
```

### Integration Tests

Requires a Kubernetes cluster with Cilium installed:

```bash
ansible-test integration --python 3.12 -v --allow-unsupported
```

## Pull Request Guidelines

- Branch from `main` and target `main` for your PR.
- Follow [conventional commit](https://www.conventionalcommits.org/) format
  for PR titles: `feat:`, `fix:`, `docs:`, `test:`, `ci:`, `refactor:`.
- Keep PRs focused on a single change.
- Include unit tests for new modules.
- Update `CHANGELOG.md` for user-facing changes.
- Ensure all CI checks pass before requesting review.

## Module Development

### Creating a New Module

1. Create the module file in `plugins/modules/`.
2. Include full `DOCUMENTATION`, `EXAMPLES`, and `RETURN` blocks.
3. Use `extends_documentation_fragment: stevefulme1.cilium.cilium_common`.
4. Use `CiliumCrdHelper` from `module_utils` for CRD management.
5. Support `check_mode`.
6. Write unit tests in `tests/unit/plugins/modules/`.
7. Create an integration test target in `tests/integration/targets/`.

### Code Style

- Maximum line length: 120 characters.
- Follow PEP 8 with exceptions defined in `ruff.toml`.
- Use `from __future__ import absolute_import, division, print_function`.
- No shebangs in module files.
