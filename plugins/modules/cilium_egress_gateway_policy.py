# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumEgressGatewayPolicy resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_egress_gateway_policy
short_description: Manage CiliumEgressGatewayPolicy resources
description:
  - Create, update, or delete CiliumEgressGatewayPolicy custom resources.
  - Routes egress traffic from selected pods through a designated gateway node with a stable external IP.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumEgressGatewayPolicy resource.
    type: str
    required: true
  selection_namespace:
    description:
      - Namespace selector or specific namespace for pods subject to this policy.
    type: dict
  selectors:
    description:
      - List of endpoint selectors for pods whose egress traffic is routed through the gateway.
    type: list
    elements: dict
  destination_cidrs:
    description:
      - List of destination CIDR blocks that trigger egress through the gateway.
    type: list
    elements: str
  egress_gateway:
    description:
      - Configuration for the egress gateway node.
      - Contains the node selector and egress IP.
    type: dict
    required: true
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Route egress traffic through gateway node
  stevefulme1.cilium.cilium_egress_gateway_policy:
    name: egress-to-external
    selectors:
      - podSelector:
          matchLabels:
            app: backend
    destination_cidrs:
      - 0.0.0.0/0
    egress_gateway:
      nodeSelector:
        matchLabels:
          egress-gateway: "true"
      egressIP: 10.0.0.100

- name: Egress policy for specific external services
  stevefulme1.cilium.cilium_egress_gateway_policy:
    name: egress-to-vendor
    selectors:
      - podSelector:
          matchLabels:
            app: payment-service
    destination_cidrs:
      - 203.0.113.0/24
      - 198.51.100.0/24
    egress_gateway:
      nodeSelector:
        matchLabels:
          node-role: egress
      egressIP: 10.0.0.200

- name: Delete egress gateway policy
  stevefulme1.cilium.cilium_egress_gateway_policy:
    name: egress-to-external
    state: absent
"""

RETURN = r"""
resource:
  description: The CiliumEgressGatewayPolicy resource dict.
  type: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client as _k8s_client  # noqa: F401
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
        selection_namespace=dict(type="dict"),
        selectors=dict(type="list", elements="dict"),
        destination_cidrs=dict(type="list", elements="str"),
        egress_gateway=dict(type="dict", required=True),
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
        plural="ciliumegressgatewaypolicies",
        kind="CiliumEgressGatewayPolicy",
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
    """Build CiliumEgressGatewayPolicy body."""
    spec = {
        "egressGateway": module.params["egress_gateway"],
    }
    if module.params.get("selectors"):
        spec["selectors"] = module.params["selectors"]
    if module.params.get("destination_cidrs"):
        spec["destinationCIDRs"] = module.params["destination_cidrs"]
    if module.params.get("selection_namespace"):
        spec["selectionNamespace"] = module.params["selection_namespace"]

    return {
        "apiVersion": "cilium.io/v2",
        "kind": "CiliumEgressGatewayPolicy",
        "metadata": build_metadata(module, cluster_scoped=True),
        "spec": spec,
    }


if __name__ == "__main__":
    main()
