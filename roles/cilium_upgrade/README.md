# cilium_upgrade

Orchestrated Cilium upgrade workflow with pre-flight and post-upgrade validation.

## Requirements

- Cilium already installed in the cluster
- `kubernetes.core` collection installed

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cilium_upgrade_namespace` | `kube-system` | Cilium namespace |
| `cilium_upgrade_target_version` | (required) | Target version |
| `cilium_upgrade_pre_flight_check` | `true` | Run pre-flight validation |
| `cilium_upgrade_post_upgrade_test` | `true` | Run post-upgrade test |
| `cilium_upgrade_rolling_restart` | `true` | Rolling restart pods |
| `cilium_upgrade_kubeconfig` | `~/.kube/config` | Path to kubeconfig |
| `cilium_upgrade_wait` | `true` | Wait for completion |
| `cilium_upgrade_wait_timeout` | `600` | Wait timeout in seconds |

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.cilium.cilium_upgrade
      cilium_upgrade_target_version: "1.17.0"
      cilium_upgrade_pre_flight_check: true
      cilium_upgrade_post_upgrade_test: true
```

## License

Apache-2.0
