# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumClusterwideNetworkPolicy resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_clusterwide_network_policy
short_description: Manage CiliumClusterwideNetworkPolicy resources
description:
  - Create, update, or delete CiliumClusterwideNetworkPolicy custom resources.
  - Cluster-scoped policies that apply across all namespaces.
  - Supports node selectors for host-level network policies.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumClusterwideNetworkPolicy resource.
    type: str
    required: true
  endpoint_selector:
    description:
      - Label selector for endpoints this policy applies to.
    type: dict
    default: {}
  node_selector:
    description:
      - Label selector for nodes (host policies).
    type: dict
  ingress:
    description:
      - List of ingress rules.
    type: list
    elements: dict
  egress:
    description:
      - List of egress rules.
    type: list
    elements: dict
  ingress_deny:
    description:
      - List of ingress deny rules.
    type: list
    elements: dict
  egress_deny:
    description:
      - List of egress deny rules.
    type: list
    elements: dict
  description:
    description:
      - Human-readable description of the policy.
    type: str
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Create cluster-wide deny-all ingress policy
  stevefulme1.cilium.cilium_clusterwide_network_policy:
    name: deny-all-ingress
    endpoint_selector: {}
    ingress_deny:
      - fromEntities:
          - world

- name: Allow DNS for all pods cluster-wide
  stevefulme1.cilium.cilium_clusterwide_network_policy:
    name: allow-dns
    endpoint_selector: {}
    egress:
      - toEndpoints:
          - matchLabels:
              k8s:io.kubernetes.pod.namespace: kube-system
              k8s-app: kube-dns
        toPorts:
          - ports:
              - port: "53"
                protocol: ANY

- name: Host-level firewall rule using node selector
  stevefulme1.cilium.cilium_clusterwide_network_policy:
    name: host-firewall
    node_selector:
      matchLabels:
        node-role.kubernetes.io/worker: ""
    ingress:
      - fromEntities:
          - cluster
        toPorts:
          - ports:
              - port: "22"
                protocol: TCP
"""

RETURN = r"""
resource:
  description: The CiliumClusterwideNetworkPolicy resource dict.
  type: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False

from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_common import (
    CILIUM_COMMON_ARGS,
    build_metadata,
    to_dict,
)
from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_k8s import CiliumCrdHelper


def main():
    argument_spec = dict(
        name=dict(type="str", required=True),
        endpoint_selector=dict(type="dict", default={}),
        node_selector=dict(type="dict"),
        ingress=dict(type="list", elements="dict"),
        egress=dict(type="list", elements="dict"),
        ingress_deny=dict(type="list", elements="dict"),
        egress_deny=dict(type="list", elements="dict"),
        description=dict(type="str"),
    )
    argument_spec.update(CILIUM_COMMON_ARGS)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_K8S_SDK:
        module.fail_json(msg="kubernetes Python SDK is required")

    helper = CiliumCrdHelper(
        module,
        group="cilium.io",
        version="v2",
        plural="ciliumclusterwidenetworkpolicies",
        kind="CiliumClusterwideNetworkPolicy",
        cluster_scoped=True,
    )

    state = module.params["state"]
    name = module.params["name"]

    existing = helper.get(name)

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        helper.delete(name)
        module.exit_json(changed=True)

    body = _build_resource(module)
    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True, resource=body)
        result = helper.create(body)
        module.exit_json(changed=True, resource=to_dict(result))

    if helper.needs_update(existing, body):
        if module.check_mode:
            module.exit_json(changed=True, resource=body)
        result = helper.update(name, body)
        module.exit_json(changed=True, resource=to_dict(result))

    module.exit_json(changed=False, resource=to_dict(existing))


def _build_resource(module):
    """Build CiliumClusterwideNetworkPolicy body."""
    spec = {}
    if module.params.get("node_selector"):
        spec["nodeSelector"] = module.params["node_selector"]
    else:
        spec["endpointSelector"] = module.params["endpoint_selector"]
    if module.params.get("ingress"):
        spec["ingress"] = module.params["ingress"]
    if module.params.get("egress"):
        spec["egress"] = module.params["egress"]
    if module.params.get("ingress_deny"):
        spec["ingressDeny"] = module.params["ingress_deny"]
    if module.params.get("egress_deny"):
        spec["egressDeny"] = module.params["egress_deny"]
    if module.params.get("description"):
        spec["description"] = module.params["description"]

    return {
        "apiVersion": "cilium.io/v2",
        "kind": "CiliumClusterwideNetworkPolicy",
        "metadata": build_metadata(module, cluster_scoped=True),
        "spec": spec,
    }


if __name__ == "__main__":
    main()
