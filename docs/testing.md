# Testing

## Prerequisites

```bash
pip install ansible-core>=2.16 kubernetes grpcio pytest pytest-cov yamllint flake8 ansible-lint
```

## Linting

```bash
yamllint -c .yamllint .
flake8 plugins/ --max-line-length=120 --ignore=E402,W503
ansible-lint --strict
```

## Sanity Tests

```bash
ansible-test sanity --python 3.12 --color yes -v
```

## Unit Tests

```bash
pytest tests/unit/ -v --tb=short
```

## Integration Tests (Mock)

Requires a Kind cluster:

```bash
kind create cluster --name cilium-test
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium --namespace kube-system --wait

ansible-test integration --python 3.12 --color yes -v --allow-unsupported
```

## Using Nox

```bash
nox -s lint
nox -s unit
```
