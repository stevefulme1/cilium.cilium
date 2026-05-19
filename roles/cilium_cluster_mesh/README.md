# cilium_cluster_mesh

Configure Cilium Cluster Mesh for multi-cluster networking.

## Requirements

- Cilium installed on all participating clusters
- `kubernetes.core` collection installed

## Role Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `cilium_cluster_mesh_namespace` | `kube-system` | Cilium namespace |
| `cilium_cluster_mesh_service_type` | `ClusterIP` | API server service type |
| `cilium_cluster_mesh_enable_endpoint_slice` | `true` | Enable EndpointSlice sync |
| `cilium_cluster_mesh_remote_contexts` | `[]` | Remote cluster contexts to connect |
| `cilium_cluster_mesh_kubeconfig` | `~/.kube/config` | Path to kubeconfig |
| `cilium_cluster_mesh_wait` | `true` | Wait for readiness |
| `cilium_cluster_mesh_wait_timeout` | `300` | Wait timeout in seconds |
| `cilium_cluster_mesh_state` | `present` | Desired state |

## Example Playbook

```yaml
- hosts: localhost
  roles:
    - role: stevefulme1.cilium.cilium_cluster_mesh
      cilium_cluster_mesh_service_type: LoadBalancer
      cilium_cluster_mesh_remote_contexts:
        - cluster-2
        - cluster-3
```

## License

Apache-2.0
