# cilium_security_hardening

Apply Tetragon TracingPolicies and network policies for comprehensive security hardening.

## Requirements

- Tetragon installed in the cluster
- `kubernetes.core` collection installed

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cilium_security_hardening_namespace` | `kube-system` | Namespace |
| `cilium_security_hardening_block_privilege_escalation` | `true` | Monitor privilege escalation |
| `cilium_security_hardening_monitor_sensitive_files` | `true` | Monitor sensitive file access |
| `cilium_security_hardening_restrict_network_tools` | `true` | Monitor network tool usage |
| `cilium_security_hardening_kubeconfig` | `~/.kube/config` | Path to kubeconfig |
| `cilium_security_hardening_state` | `present` | Desired state |

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.cilium.cilium_security_hardening
      cilium_security_hardening_block_privilege_escalation: true
      cilium_security_hardening_monitor_sensitive_files: true
      cilium_security_hardening_restrict_network_tools: true
```

## License

Apache-2.0
