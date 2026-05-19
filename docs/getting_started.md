# Getting Started

## Prerequisites

- A Kubernetes cluster (v1.25+)
- `kubectl` configured with cluster access
- Helm v3 installed (for `cilium_install` and `cilium_upgrade` modules)
- Python 3.12+ with `kubernetes` SDK installed

## Install the Collection

```bash
ansible-galaxy collection install stevefulme1.cilium
pip install kubernetes>=28.1.0
```

## Deploy Cilium

The fastest way to deploy Cilium is using the `cilium_install` role:

```yaml
---
- name: Deploy Cilium CNI
  hosts: localhost
  connection: local
  roles:
    - role: stevefulme1.cilium.cilium_install
      cilium_install_chart_version: "1.17.0"
      cilium_install_hubble_enabled: true
```

## Verify Deployment

```yaml
---
- name: Check Cilium status
  hosts: localhost
  connection: local
  tasks:
    - name: Get Cilium status
      stevefulme1.cilium.cilium_status_info: {}
      register: cilium_status

    - name: Display status
      ansible.builtin.debug:
        var: cilium_status.resource
```

## Apply Network Policies

```yaml
---
- name: Apply baseline network policies
  hosts: localhost
  connection: local
  roles:
    - role: stevefulme1.cilium.cilium_network_baseline
      cilium_network_baseline_deny_all_ingress: true
      cilium_network_baseline_allow_dns: true
```

## Enable Observability

```yaml
---
- name: Enable Hubble observability
  hosts: localhost
  connection: local
  roles:
    - role: stevefulme1.cilium.cilium_hubble
      cilium_hubble_relay_enabled: true
      cilium_hubble_ui_enabled: true
```
