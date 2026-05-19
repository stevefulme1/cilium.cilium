# cilium_network_baseline

Apply baseline Cilium network policies for zero-trust networking.

## Requirements

- Cilium installed in the cluster
- `kubernetes.core` collection installed

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cilium_network_baseline_namespace` | `kube-system` | Cilium namespace |
| `cilium_network_baseline_deny_all_ingress` | `true` | Default deny ingress |
| `cilium_network_baseline_allow_dns` | `true` | Allow DNS traffic |
| `cilium_network_baseline_allow_health_checks` | `true` | Allow health checks |
| `cilium_network_baseline_target_namespaces` | `[]` | Specific namespaces |
| `cilium_network_baseline_state` | `present` | Desired state |

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.cilium.cilium_network_baseline
      cilium_network_baseline_deny_all_ingress: true
      cilium_network_baseline_allow_dns: true
```

## License

Apache-2.0
