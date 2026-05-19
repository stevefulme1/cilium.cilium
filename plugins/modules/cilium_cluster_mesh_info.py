# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying Cluster Mesh status."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_cluster_mesh_info
short_description: Query Cilium Cluster Mesh status
description:
  - Retrieve Cluster Mesh status, connected clusters, and health information.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  namespace:
    description:
      - Kubernetes namespace where Cilium is installed.
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
"""

EXAMPLES = r"""
- name: Get Cluster Mesh status
  stevefulme1.cilium.cilium_cluster_mesh_info:
  register: mesh_status

- name: Check Cluster Mesh in custom namespace
  stevefulme1.cilium.cilium_cluster_mesh_info:
    namespace: cilium-system
  register: mesh_status

- name: Display mesh info
  stevefulme1.cilium.cilium_cluster_mesh_info:
  register: mesh
- debug:
    var: mesh.status
"""

RETURN = r"""
status:
  description: Cluster Mesh status information.
  type: dict
  returned: always
  contains:
    enabled:
      description: Whether Cluster Mesh is enabled.
      type: bool
    apiserver_ready:
      description: Whether the Cluster Mesh API server is ready.
      type: bool
    connected_clusters:
      description: List of connected remote clusters.
      type: list
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config  # noqa: F401
    from kubernetes.client.rest import ApiException
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False


def main():
    argument_spec = dict(
        namespace=dict(type="str", default="kube-system"),
        kubeconfig=dict(type="str"),
        context=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_K8S_SDK:
        module.fail_json(msg="kubernetes Python SDK is required")

    kubeconfig = module.params.get("kubeconfig")
    ctx = module.params.get("context")
    try:
        if kubeconfig:
            config.load_kube_config(config_file=kubeconfig, context=ctx)
        else:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config(context=ctx)
    except Exception as e:
        module.fail_json(msg="Failed to load kubeconfig: %s" % str(e))

    apps_api = client.AppsV1Api()
    core_api = client.CoreV1Api()
    namespace = module.params["namespace"]

    status = {
        "enabled": False,
        "apiserver_ready": False,
        "connected_clusters": [],
    }

    # Check clustermesh-apiserver deployment
    try:
        deploy = apps_api.read_namespaced_deployment(
            "clustermesh-apiserver", namespace
        )
        st = deploy.status
        status["enabled"] = True
        status["apiserver_ready"] = (st.ready_replicas or 0) > 0
        status["apiserver_replicas"] = {
            "desired": st.replicas or 0,
            "ready": st.ready_replicas or 0,
        }
    except ApiException:
        pass

    # Check for remote cluster secrets
    try:
        secrets = core_api.list_namespaced_secret(
            namespace,
            label_selector="clustermesh.cilium.io/remote-cluster",
        )
        for secret in secrets.items:
            cluster_name = secret.metadata.labels.get(
                "clustermesh.cilium.io/remote-cluster", "unknown"
            )
            status["connected_clusters"].append({
                "name": cluster_name,
                "secret": secret.metadata.name,
            })
    except ApiException:
        pass

    module.exit_json(changed=False, status=status)


if __name__ == "__main__":
    main()
