# Pull Request Review Checklist

Use this checklist when reviewing pull requests for the `stevefulme1.cilium`
Ansible collection.

## General

- [ ] PR title follows conventional commit format (`feat:`, `fix:`, `docs:`, etc.)
- [ ] PR description clearly explains the change and its motivation
- [ ] No unrelated changes included in the PR

## Code Quality

- [ ] flake8 passes (`--max-line-length=120 --ignore=E402,W503`)
- [ ] yamllint passes
- [ ] ansible-lint passes with `--strict`
- [ ] No shebangs in module files
- [ ] Imports are placed after DOCUMENTATION/EXAMPLES/RETURN blocks
- [ ] No hardcoded credentials or secrets
- [ ] Sensitive parameters use `no_log=True` in argument_spec only

## Modules

- [ ] `DOCUMENTATION` block is complete with all options documented
- [ ] `EXAMPLES` block has at least two examples
- [ ] `RETURN` block documents all return values
- [ ] `extends_documentation_fragment: stevefulme1.cilium.cilium_common`
- [ ] `supports_check_mode=True`
- [ ] Uses `CiliumCrdHelper` or `CiliumHelmHelper` from module_utils
- [ ] CRD group, version, and plural are correct for the target resource
- [ ] Idempotent: get -> compare -> create/update/noop pattern
- [ ] Proper error handling with `module.fail_json(msg=...)`

## Roles

- [ ] `meta/main.yml` has correct galaxy_info
- [ ] `meta/argument_specs.yml` documents all role parameters
- [ ] `defaults/main.yml` prefixes all vars with role name
- [ ] `tasks/main.yml` starts with parameter validation
- [ ] `README.md` documents the role

## Tests

- [ ] Unit tests cover create, update, delete, and idempotency
- [ ] Integration tests follow create-verify-idempotency-update-delete pattern
- [ ] No real cluster credentials in test files
