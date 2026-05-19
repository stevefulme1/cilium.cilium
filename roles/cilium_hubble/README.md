# cilium_hubble

Deploy and configure the Hubble observability stack for Cilium.

## Requirements

- Cilium already installed in the cluster
- `kubernetes.core` collection installed

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cilium_hubble_namespace` | `kube-system` | Cilium namespace |
| `cilium_hubble_relay_enabled` | `true` | Enable Hubble Relay |
| `cilium_hubble_ui_enabled` | `true` | Enable Hubble UI |
| `cilium_hubble_metrics` | `[dns,drop,tcp,flow,icmp,http]` | Metrics to enable |
| `cilium_hubble_helm_release_name` | `cilium` | Helm release name |
| `cilium_hubble_kubeconfig` | `~/.kube/config` | Path to kubeconfig |
| `cilium_hubble_wait` | `true` | Wait for readiness |
| `cilium_hubble_wait_timeout` | `300` | Wait timeout in seconds |

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.cilium.cilium_hubble
      cilium_hubble_ui_enabled: true
      cilium_hubble_metrics:
        - dns
        - drop
        - tcp
        - flow
        - http
```

## License

Apache-2.0
