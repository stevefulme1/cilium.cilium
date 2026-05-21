# Changelog

All notable changes to this collection will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-05-20

### Fixed

- Renamed reserved `values` return key to `helm_values` in `cilium_cluster_mesh`
  and `cilium_hubble` modules (ansible-test validate-modules).
- Fixed parameter mismatches between role tasks and module argument specs:
  - `cilium_cluster_mesh` role: replaced `remote_context`/`state` with
    `enabled`/`remote_clusters`.
  - `cilium_observability` role: replaced `metrics`/`state` with `hubble_metrics`.
  - `cilium_upgrade` role: replaced `namespace` with `cilium_namespace` for
    connectivity test tasks.
  - `examples/observability/enable_hubble.yml`: replaced `metrics`/`state`
    with `hubble_metrics`.
- Added `.ansible/` to `.gitignore`.

## [1.0.0] - 2025-05-19 [YANKED]

### Added

- Initial release of the `stevefulme1.cilium` Ansible collection.

#### Modules (31)

- **Networking**: `cilium_install`, `cilium_upgrade`, `cilium_config`,
  `cilium_network_policy`, `cilium_network_policy_info`,
  `cilium_clusterwide_network_policy`, `cilium_clusterwide_network_policy_info`,
  `cilium_bgp_peering_policy`, `cilium_lb_ip_pool`,
  `cilium_local_redirect_policy`, `cilium_egress_gateway_policy`,
  `cilium_cidr_group`.
- **L7 Proxy**: `cilium_envoy_config`, `cilium_clusterwide_envoy_config`,
  `cilium_envoy_config_info`.
- **Observability**: `cilium_hubble`, `cilium_hubble_info`,
  `cilium_metrics_config`, `cilium_service_map_info`.
- **Security / Tetragon**: `cilium_tracing_policy`, `cilium_tracing_policy_info`,
  `cilium_tracing_policy_namespaced`, `cilium_tracing_policy_namespaced_info`.
- **Cluster Management**: `cilium_cluster_mesh`, `cilium_cluster_mesh_info`,
  `cilium_node_config`, `cilium_connectivity_test`.
- **Identity / Endpoint**: `cilium_endpoint_info`, `cilium_identity_info`,
  `cilium_service_info`, `cilium_status_info`.

#### Roles (8)

- `cilium_install` -- Full Cilium CNI deployment.
- `cilium_hubble` -- Hubble observability stack.
- `cilium_tetragon` -- Tetragon runtime security with baseline policies.
- `cilium_cluster_mesh` -- Multi-cluster Cluster Mesh setup.
- `cilium_upgrade` -- Orchestrated upgrade workflow.
- `cilium_observability` -- Full observability stack.
- `cilium_network_baseline` -- Baseline network policies.
- `cilium_security_hardening` -- Security hardening with Tetragon.

#### EDA Event Source Plugins (3)

- `cilium_policy_event` -- Stream Hubble policy violation events.
- `cilium_hubble_flow` -- Stream Hubble network flow events.
- `cilium_tetragon_event` -- Stream Tetragon runtime security events.

#### Other

- Filter plugins: `cilium_endpoint_status`, `cilium_policy_verdict`,
  `cilium_identity_labels`.
- Documentation fragment: `cilium_common`.
- Full CI pipeline with lint, sanity, unit, and integration tests.
