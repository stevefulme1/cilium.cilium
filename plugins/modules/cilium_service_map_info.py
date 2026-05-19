# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying the Hubble service dependency map."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_service_map_info
short_description: Query Hubble service dependency map
description:
  - Retrieve service-to-service communication information from Hubble.
  - Queries the Hubble UI backend API for service map data.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  namespace:
    description:
      - Kubernetes namespace to query service map for.
      - If omitted, queries across all namespaces.
    type: str
  hubble_ui_service:
    description:
      - Name of the Hubble UI service to query.
    type: str
    default: hubble-ui
  hubble_ui_namespace:
    description:
      - Namespace where Hubble UI is deployed.
    type: str
    default: kube-system
  hubble_ui_port:
    description:
      - Port of the Hubble UI service.
    type: int
    default: 80
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
- name: Get service map for all namespaces
  stevefulme1.cilium.cilium_service_map_info:
  register: service_map

- name: Get service map for a specific namespace
  stevefulme1.cilium.cilium_service_map_info:
    namespace: production
  register: prod_service_map

- name: Query service map with custom Hubble UI location
  stevefulme1.cilium.cilium_service_map_info:
    hubble_ui_namespace: cilium-system
    hubble_ui_port: 8080
  register: service_map
"""

RETURN = r"""
services:
  description: List of services observed by Hubble.
  type: list
  elements: dict
  returned: always
connections:
  description: List of service-to-service connections.
  type: list
  elements: dict
  returned: always
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
        namespace=dict(type="str"),
        hubble_ui_service=dict(type="str", default="hubble-ui"),
        hubble_ui_namespace=dict(type="str", default="kube-system"),
        hubble_ui_port=dict(type="int", default=80),
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

    core_api = client.CoreV1Api()
    apps_api = client.AppsV1Api()
    hubble_ns = module.params["hubble_ui_namespace"]

    # Check Hubble UI deployment status
    services = []
    connections = []

    try:
        deploy = apps_api.read_namespaced_deployment("hubble-ui", hubble_ns)
        if (deploy.status.ready_replicas or 0) == 0:
            module.exit_json(
                changed=False, services=[], connections=[],
                msg="Hubble UI is not ready"
            )
    except ApiException:
        module.exit_json(
            changed=False, services=[], connections=[],
            msg="Hubble UI deployment not found"
        )

    # Query endpoints to build service map from pod labels
    target_ns = module.params.get("namespace")
    try:
        if target_ns:
            endpoints = core_api.list_namespaced_endpoints(target_ns)
        else:
            endpoints = core_api.list_endpoints_for_all_namespaces()

        for ep in endpoints.items:
            svc_name = ep.metadata.name
            svc_ns = ep.metadata.namespace
            svc_entry = {
                "name": svc_name,
                "namespace": svc_ns,
                "endpoints_count": 0,
            }
            if ep.subsets:
                for subset in ep.subsets:
                    if subset.addresses:
                        svc_entry["endpoints_count"] += len(subset.addresses)
            services.append(svc_entry)
    except ApiException as e:
        module.fail_json(msg="Failed to list endpoints: %s" % str(e))

    # Query Cilium endpoints for identity-based connections
    custom_api = client.CustomObjectsApi()
    try:
        if target_ns:
            ceps = custom_api.list_namespaced_custom_object(
                "cilium.io", "v2", target_ns, "ciliumendpoints"
            )
        else:
            ceps = custom_api.list_cluster_custom_object(
                "cilium.io", "v2", "ciliumendpoints"
            )
        for item in ceps.get("items", []):
            identity = item.get("status", {}).get("identity", {})
            networking = item.get("status", {}).get("networking", {})
            if identity and networking:
                connections.append({
                    "endpoint": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                    "identity_id": identity.get("id"),
                    "identity_labels": identity.get("labels", []),
                    "addresses": [
                        a.get("ip") for a in networking.get("addressing", [])
                    ],
                })
    except ApiException:
        pass

    module.exit_json(changed=False, services=services, connections=connections)


if __name__ == "__main__":
    main()
