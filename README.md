# Cilium CNI Ansible Collection

[![CI](https://github.com/stevefulme1/cilium.cilium/actions/workflows/ci.yml/badge.svg)](https://github.com/stevefulme1/cilium.cilium/actions/workflows/ci.yml)

Ansible Collection for managing Cilium CNI, Hubble observability, Tetragon
runtime security, and Isovalent Enterprise. Provides 31 modules, 8 roles,
3 EDA event source plugins, and filter plugins covering networking, L7 proxy,
security, observability, cluster mesh, and Day 2 operations.

## Requirements

| Dependency | Version |
|---|---|
| Python | >= 3.12 |
| ansible-core | >= 2.16.0 |
| kubernetes Python SDK | >= 28.1.0 |
| grpcio (optional, for EDA) | >= 1.60.0 |

### Collection Dependencies

| Collection | Version |
|---|---|
| kubernetes.core | >= 3.0.0 |

## Installation

```bash
ansible-galaxy collection install stevefulme1.cilium
```

Install Python dependencies:

```bash
pip install kubernetes>=28.1.0 grpcio>=1.60.0
```

## Authentication

Configure Kubernetes credentials using one of the following methods:

1. **Kubeconfig file** (default): `~/.kube/config`
2. **Environment variable**: `KUBECONFIG=/path/to/config`
3. **In-cluster**: Automatic when running inside a Kubernetes pod
4. **Service account token**: Provide `kubeconfig` and `context` parameters

All modules accept the common authentication parameters defined in the
`stevefulme1.cilium.cilium_common` documentation fragment.

## Modules

### Networking

| Module | Description |
|---|---|
| `cilium_install` | Deploy Cilium via Helm |
| `cilium_upgrade` | Upgrade Cilium with pre-flight checks |
| `cilium_config` | Manage cilium-config ConfigMap |
| `cilium_network_policy` | Manage CiliumNetworkPolicy CRDs |
| `cilium_network_policy_info` | Query CiliumNetworkPolicy resources |
| `cilium_clusterwide_network_policy` | Manage CiliumClusterwideNetworkPolicy |
| `cilium_clusterwide_network_policy_info` | Query cluster-wide policies |
| `cilium_bgp_peering_policy` | Manage CiliumBGPPeeringPolicy |
| `cilium_lb_ip_pool` | Manage CiliumLoadBalancerIPPool |
| `cilium_local_redirect_policy` | Manage CiliumLocalRedirectPolicy |
| `cilium_egress_gateway_policy` | Manage CiliumEgressGatewayPolicy |
| `cilium_cidr_group` | Manage CiliumCIDRGroup |

### L7 Proxy

| Module | Description |
|---|---|
| `cilium_envoy_config` | Manage CiliumEnvoyConfig |
| `cilium_clusterwide_envoy_config` | Manage CiliumClusterwideEnvoyConfig |
| `cilium_envoy_config_info` | Query Envoy configurations |

### Observability

| Module | Description |
|---|---|
| `cilium_hubble` | Enable and configure Hubble |
| `cilium_hubble_info` | Query Hubble status and flow data |
| `cilium_metrics_config` | Configure Prometheus metrics |
| `cilium_service_map_info` | Query Hubble service dependency map |

### Security / Tetragon

| Module | Description |
|---|---|
| `cilium_tracing_policy` | Manage Tetragon TracingPolicy |
| `cilium_tracing_policy_info` | Query TracingPolicy resources |
| `cilium_tracing_policy_namespaced` | Manage namespace-scoped TracingPolicy |
| `cilium_tracing_policy_namespaced_info` | Query namespace-scoped TracingPolicy |

### Cluster Management

| Module | Description |
|---|---|
| `cilium_cluster_mesh` | Configure Cluster Mesh |
| `cilium_cluster_mesh_info` | Query Cluster Mesh status |
| `cilium_node_config` | Manage CiliumNodeConfig |
| `cilium_connectivity_test` | Run connectivity validation |

### Identity and Endpoint

| Module | Description |
|---|---|
| `cilium_endpoint_info` | Query CiliumEndpoint resources |
| `cilium_identity_info` | Query Cilium security identities |
| `cilium_service_info` | Query Cilium-managed services |
| `cilium_status_info` | Query Cilium agent and operator health |

## Roles

| Role | Description |
|---|---|
| `cilium_install` | Full Cilium CNI deployment with best-practice defaults |
| `cilium_hubble` | Hubble observability stack (Server + Relay + UI) |
| `cilium_tetragon` | Tetragon runtime security with baseline policies |
| `cilium_cluster_mesh` | Multi-cluster Cluster Mesh setup with CA management |
| `cilium_upgrade` | Orchestrated upgrade with pre-flight and post-upgrade validation |
| `cilium_observability` | Full observability stack (Hubble + Prometheus + Grafana) |
| `cilium_network_baseline` | Baseline network policies (default deny + essential allows) |
| `cilium_security_hardening` | Security hardening (Tetragon + network policies) |

## EDA Event Source Plugins

| Plugin | Description |
|---|---|
| `cilium_policy_event` | Stream Hubble policy violation events |
| `cilium_hubble_flow` | Stream Hubble network flow events |
| `cilium_tetragon_event` | Stream Tetragon runtime security events |

## Filter Plugins

| Filter | Description |
|---|---|
| `cilium_endpoint_status` | Extract endpoint status from Cilium objects |
| `cilium_policy_verdict` | Parse policy verdicts from Hubble flows |
| `cilium_identity_labels` | Extract security identity labels |

## Quick Start

### Deploy Cilium

```yaml
- name: Deploy Cilium CNI
  hosts: localhost
  roles:
    - role: stevefulme1.cilium.cilium_install
      cilium_install_chart_version: "1.17.0"
      cilium_install_kube_proxy_replacement: true
      cilium_install_hubble_enabled: true
```

### Apply Network Policy

```yaml
- name: Apply network policy
  stevefulme1.cilium.cilium_network_policy:
    name: allow-web-traffic
    namespace: default
    endpoint_selector:
      matchLabels:
        app: web
    ingress:
      - fromEndpoints:
          - matchLabels:
              app: frontend
        toPorts:
          - ports:
              - port: "80"
                protocol: TCP
    state: present
```

### EDA Rulebook Example

```yaml
---
- name: Respond to Cilium policy violations
  hosts: all
  sources:
    - stevefulme1.cilium.cilium_policy_event:
        hubble_endpoint: "hubble-relay.kube-system:4245"
  rules:
    - name: Log policy violation
      condition: event.verdict == "DROPPED"
      action:
        run_playbook:
          name: remediate_policy_violation.yml
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

GNU General Public License v3.0 or later.
See [COPYING](COPYING) for the full license text.
