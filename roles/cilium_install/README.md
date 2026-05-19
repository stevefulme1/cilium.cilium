# cilium_install

Deploy Cilium CNI via Helm with full configuration support.

## Requirements

- Kubernetes cluster accessible via kubeconfig
- Helm 3.x
- `kubernetes.core` collection installed

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cilium_install_namespace` | `kube-system` | Target namespace |
| `cilium_install_chart_version` | `1.17.0` | Helm chart version |
| `cilium_install_helm_repo` | `https://helm.cilium.io/` | Helm repository URL |
| `cilium_install_helm_release_name` | `cilium` | Helm release name |
| `cilium_install_kube_proxy_replacement` | `true` | Enable kube-proxy replacement |
| `cilium_install_hubble_enabled` | `true` | Enable Hubble observability |
| `cilium_install_kubeconfig` | `~/.kube/config` | Path to kubeconfig |
| `cilium_install_context` | `""` | Kubernetes context |
| `cilium_install_wait` | `true` | Wait for deployment readiness |
| `cilium_install_wait_timeout` | `300` | Wait timeout in seconds |
| `cilium_install_state` | `present` | Desired state |

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.cilium.cilium_install
      cilium_install_chart_version: "1.17.0"
      cilium_install_kube_proxy_replacement: true
```

## License

Apache-2.0
