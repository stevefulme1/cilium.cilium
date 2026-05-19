# cilium_observability

Deploy the full Cilium observability stack with Hubble metrics, Prometheus, and Grafana.

## Requirements

- Cilium installed in the cluster
- Prometheus Operator (for ServiceMonitor support)
- `kubernetes.core` collection installed

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cilium_observability_namespace` | `kube-system` | Cilium namespace |
| `cilium_observability_prometheus_enabled` | `true` | Enable Prometheus |
| `cilium_observability_grafana_enabled` | `true` | Enable Grafana dashboards |
| `cilium_observability_hubble_metrics` | `[dns,drop,tcp,flow]` | Hubble metrics |
| `cilium_observability_prometheus_namespace` | `monitoring` | Prometheus namespace |
| `cilium_observability_grafana_namespace` | `monitoring` | Grafana namespace |

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.cilium.cilium_observability
      cilium_observability_prometheus_enabled: true
      cilium_observability_grafana_enabled: true
```

## License

Apache-2.0
