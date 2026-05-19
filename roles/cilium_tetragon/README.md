# cilium_tetragon

Deploy Tetragon runtime security enforcement with optional baseline TracingPolicies.

## Requirements

- Kubernetes cluster accessible via kubeconfig
- Helm 3.x
- `kubernetes.core` collection installed

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cilium_tetragon_namespace` | `kube-system` | Target namespace |
| `cilium_tetragon_chart_version` | `1.3.0` | Helm chart version |
| `cilium_tetragon_helm_repo` | `https://helm.cilium.io/` | Helm repository URL |
| `cilium_tetragon_baseline_policies_enabled` | `true` | Deploy baseline TracingPolicies |
| `cilium_tetragon_kubeconfig` | `~/.kube/config` | Path to kubeconfig |
| `cilium_tetragon_wait` | `true` | Wait for readiness |
| `cilium_tetragon_wait_timeout` | `300` | Wait timeout in seconds |
| `cilium_tetragon_state` | `present` | Desired state |

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.cilium.cilium_tetragon
      cilium_tetragon_baseline_policies_enabled: true
```

## License

Apache-2.0
