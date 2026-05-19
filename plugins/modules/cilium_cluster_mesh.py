# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for configuring Cilium Cluster Mesh."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_cluster_mesh
short_description: Configure Cilium Cluster Mesh
description:
  - Enable or disable Cluster Mesh via Helm values.
  - Configure multi-cluster connectivity for Cilium.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  enabled:
    description:
      - Whether Cluster Mesh is enabled.
    type: bool
    default: true
  service_type:
    description:
      - Kubernetes service type for the Cluster Mesh API server.
    type: str
    choices: [LoadBalancer, NodePort, ClusterIP]
    default: LoadBalancer
  remote_clusters:
    description:
      - List of remote cluster configurations to connect to.
      - Each item is a dict with name, address, and port.
    type: list
    elements: dict
  cluster_name:
    description:
      - Name of this cluster in the mesh.
    type: str
  cluster_id:
    description:
      - Unique numeric ID for this cluster (1-255).
    type: int
  release_name:
    description:
      - Helm release name for Cilium.
    type: str
    default: cilium
  namespace:
    description:
      - Namespace of the Cilium installation.
    type: str
    default: kube-system
  kubeconfig:
    description:
      - Path to a kubeconfig file.
    type: str
  context:
    description:
      - Kubernetes context to use.
    type: str
  helm_binary:
    description:
      - Path to the Helm binary.
    type: str
    default: helm
"""

EXAMPLES = r"""
- name: Enable Cluster Mesh
  stevefulme1.cilium.cilium_cluster_mesh:
    enabled: true
    cluster_name: cluster-1
    cluster_id: 1
    service_type: LoadBalancer

- name: Enable Cluster Mesh with NodePort
  stevefulme1.cilium.cilium_cluster_mesh:
    enabled: true
    cluster_name: cluster-2
    cluster_id: 2
    service_type: NodePort

- name: Disable Cluster Mesh
  stevefulme1.cilium.cilium_cluster_mesh:
    enabled: false
"""

RETURN = r"""
release:
  description: Helm release information after update.
  type: dict
  returned: always
values:
  description: Cluster Mesh Helm values applied.
  type: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client as _k8s_client  # noqa: F401
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False

from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_k8s import CiliumHelmHelper


def main():
    argument_spec = dict(
        enabled=dict(type="bool", default=True),
        service_type=dict(type="str", choices=["LoadBalancer", "NodePort", "ClusterIP"],
                          default="LoadBalancer"),
        remote_clusters=dict(type="list", elements="dict"),
        cluster_name=dict(type="str"),
        cluster_id=dict(type="int"),
        release_name=dict(type="str", default="cilium"),
        namespace=dict(type="str", default="kube-system"),
        kubeconfig=dict(type="str"),
        context=dict(type="str"),
        helm_binary=dict(type="str", default="helm"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_K8S_SDK:
        module.fail_json(msg="kubernetes Python SDK is required")

    helper = CiliumHelmHelper(module)

    release_name = module.params["release_name"]
    namespace = module.params["namespace"]

    existing = helper.get_release(release_name, namespace)
    if existing is None:
        module.fail_json(msg="Cilium release '%s' not found" % release_name)

    desired_values = {
        "clustermesh": {
            "useAPIServer": module.params["enabled"],
            "apiserver": {
                "service": {
                    "type": module.params["service_type"],
                },
            },
        },
    }

    if module.params.get("cluster_name"):
        desired_values["cluster"] = {
            "name": module.params["cluster_name"],
        }
    if module.params.get("cluster_id"):
        desired_values.setdefault("cluster", {})["id"] = module.params["cluster_id"]

    current_values = helper.get_release_values(release_name, namespace)
    if not helper.values_changed(current_values, desired_values):
        module.exit_json(changed=False, release=existing, values=desired_values)

    if module.check_mode:
        module.exit_json(changed=True, release=existing, values=desired_values)

    helper.upgrade(
        release_name, "cilium/cilium", namespace,
        values=desired_values,
    )

    release = helper.get_release(release_name, namespace) or {}
    module.exit_json(changed=True, release=release, values=desired_values)


if __name__ == "__main__":
    main()
