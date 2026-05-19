# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying K8s Services with Cilium annotations."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_service_info
short_description: Query Kubernetes Services with Cilium annotations
description:
  - Retrieve Kubernetes Services that have Cilium-specific annotations.
  - Useful for auditing LoadBalancer IP assignments, service affinity, and Cilium features.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of a specific Service to retrieve.
    type: str
  namespace:
    description:
      - Kubernetes namespace to query.
      - If omitted, queries all namespaces.
    type: str
  label_selector:
    description:
      - Label selector to filter services.
    type: str
    default: ""
  cilium_only:
    description:
      - If true, only return services with Cilium annotations.
    type: bool
    default: false
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
- name: List all services in a namespace
  stevefulme1.cilium.cilium_service_info:
    namespace: production
  register: services

- name: Get services with Cilium annotations only
  stevefulme1.cilium.cilium_service_info:
    namespace: production
    cilium_only: true
  register: cilium_services

- name: Get a specific service
  stevefulme1.cilium.cilium_service_info:
    name: my-service
    namespace: production
  register: service
"""

RETURN = r"""
resources:
  description: List of Kubernetes Service resources with Cilium annotation details.
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

from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_common import (  # noqa: F401
    to_dict,
)


def main():
    argument_spec = dict(
        name=dict(type="str"),
        namespace=dict(type="str"),
        label_selector=dict(type="str", default=""),
        cilium_only=dict(type="bool", default=False),
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
    name = module.params.get("name")
    namespace = module.params.get("namespace")
    label_selector = module.params.get("label_selector", "")
    cilium_only = module.params.get("cilium_only", False)

    services = []

    try:
        if name and namespace:
            svc = core_api.read_namespaced_service(name, namespace)
            svc_dict = _format_service(svc)
            if not cilium_only or svc_dict.get("cilium_annotations"):
                services.append(svc_dict)
        elif namespace:
            svc_list = core_api.list_namespaced_service(
                namespace, label_selector=label_selector
            )
            for svc in svc_list.items:
                svc_dict = _format_service(svc)
                if not cilium_only or svc_dict.get("cilium_annotations"):
                    services.append(svc_dict)
        else:
            svc_list = core_api.list_service_for_all_namespaces(
                label_selector=label_selector
            )
            for svc in svc_list.items:
                svc_dict = _format_service(svc)
                if not cilium_only or svc_dict.get("cilium_annotations"):
                    services.append(svc_dict)
    except ApiException as e:
        if e.status == 404:
            module.exit_json(changed=False, resources=[])
        module.fail_json(msg="Failed to query services: %s" % str(e))

    module.exit_json(changed=False, resources=services)


def _format_service(svc):
    """Format a Service object with Cilium-specific details."""
    annotations = svc.metadata.annotations or {}
    cilium_annotations = {
        k: v for k, v in annotations.items()
        if "cilium" in k.lower() or "lbipam" in k.lower()
    }

    result = {
        "name": svc.metadata.name,
        "namespace": svc.metadata.namespace,
        "type": svc.spec.type,
        "cluster_ip": svc.spec.cluster_ip,
        "external_ips": svc.spec.external_i_ps or [],
        "ports": [],
        "labels": svc.metadata.labels or {},
        "annotations": annotations,
        "cilium_annotations": cilium_annotations,
    }

    if svc.status and svc.status.load_balancer and svc.status.load_balancer.ingress:
        result["load_balancer_ips"] = [
            ing.ip or ing.hostname
            for ing in svc.status.load_balancer.ingress
        ]
    else:
        result["load_balancer_ips"] = []

    if svc.spec.ports:
        for port in svc.spec.ports:
            result["ports"].append({
                "name": port.name,
                "port": port.port,
                "target_port": str(port.target_port),
                "protocol": port.protocol,
                "node_port": port.node_port,
            })

    return result


if __name__ == "__main__":
    main()
