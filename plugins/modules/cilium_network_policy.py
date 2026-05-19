# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumNetworkPolicy resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_network_policy
short_description: Manage CiliumNetworkPolicy resources
description:
  - Create, update, or delete CiliumNetworkPolicy custom resources.
  - CiliumNetworkPolicy extends Kubernetes NetworkPolicy with Cilium-specific
    features including L7 rules, DNS-based policies, and identity-based matching.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumNetworkPolicy resource.
    type: str
    required: true
  endpoint_selector:
    description:
      - Label selector for endpoints this policy applies to.
      - Uses the same format as Kubernetes label selectors.
    type: dict
    default: {}
  ingress:
    description:
      - List of ingress rules.
      - Each rule can specify fromEndpoints, fromCIDR, toPorts, etc.
    type: list
    elements: dict
  egress:
    description:
      - List of egress rules.
      - Each rule can specify toEndpoints, toCIDR, toPorts, toFQDNs, etc.
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
- name: Allow HTTP traffic from frontend to backend
  stevefulme1.cilium.cilium_network_policy:
    name: allow-frontend-to-backend
    namespace: production
    endpoint_selector:
      matchLabels:
        app: backend
    ingress:
      - fromEndpoints:
          - matchLabels:
              app: frontend
        toPorts:
          - ports:
              - port: "80"
                protocol: TCP
            rules:
              http:
                - method: GET
                  path: "/api/.*"

- name: Restrict egress to specific CIDR
  stevefulme1.cilium.cilium_network_policy:
    name: restrict-egress
    namespace: production
    endpoint_selector:
      matchLabels:
        app: worker
    egress:
      - toCIDR:
          - 10.0.0.0/8
        toPorts:
          - ports:
              - port: "443"
                protocol: TCP

- name: Delete a network policy
  stevefulme1.cilium.cilium_network_policy:
    name: allow-frontend-to-backend
    namespace: production
    state: absent
"""

RETURN = r"""
resource:
  description: The CiliumNetworkPolicy resource dict.
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
        endpoint_selector=dict(type="dict", default={}),
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
        plural="ciliumnetworkpolicies",
        kind="CiliumNetworkPolicy",
    )

    state = module.params["state"]
    name = module.params["name"]
    namespace = module.params["namespace"]

    existing = helper.get(name, namespace)

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False)
        if module.check_mode:
            module.exit_json(changed=True)
        helper.delete(name, namespace)
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
        result = helper.update(name, body, namespace)
        module.exit_json(changed=True, resource=to_dict(result))

    module.exit_json(changed=False, resource=to_dict(existing))


def _build_resource(module):
    """Build CiliumNetworkPolicy body from module params."""
    spec = {"endpointSelector": module.params["endpoint_selector"]}
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
        "kind": "CiliumNetworkPolicy",
        "metadata": build_metadata(module),
        "spec": spec,
    }


if __name__ == "__main__":
    main()
