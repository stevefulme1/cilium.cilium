# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumBGPPeeringPolicy resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_bgp_peering_policy
short_description: Manage CiliumBGPPeeringPolicy resources
description:
  - Create, update, or delete CiliumBGPPeeringPolicy custom resources.
  - Configures BGP peering for Cilium nodes to advertise routes and services.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumBGPPeeringPolicy resource.
    type: str
    required: true
  node_selector:
    description:
      - Label selector to match Kubernetes nodes for BGP peering.
    type: dict
    required: true
  virtual_routers:
    description:
      - List of virtual router configurations.
      - Each virtual router defines a local ASN, export policies, and neighbors.
    type: list
    elements: dict
    required: true
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Create BGP peering policy
  stevefulme1.cilium.cilium_bgp_peering_policy:
    name: bgp-peering
    node_selector:
      matchLabels:
        bgp-policy: rack1
    virtual_routers:
      - localASN: 65001
        exportPodCIDR: true
        neighbors:
          - peerAddress: 10.0.0.1/32
            peerASN: 65000
            eBGPMultihopTTL: 10
            connectRetryTimeSeconds: 120
            holdTimeSeconds: 90
            keepAliveTimeSeconds: 30

- name: BGP policy with service advertisement
  stevefulme1.cilium.cilium_bgp_peering_policy:
    name: bgp-services
    node_selector:
      matchLabels:
        node-role.kubernetes.io/worker: ""
    virtual_routers:
      - localASN: 65001
        exportPodCIDR: false
        serviceSelector:
          matchExpressions:
            - key: app
              operator: In
              values: ["web", "api"]
        neighbors:
          - peerAddress: 192.168.1.1/32
            peerASN: 65000

- name: Delete BGP peering policy
  stevefulme1.cilium.cilium_bgp_peering_policy:
    name: bgp-peering
    state: absent
"""

RETURN = r"""
resource:
  description: The CiliumBGPPeeringPolicy resource dict.
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
        node_selector=dict(type="dict", required=True),
        virtual_routers=dict(type="list", elements="dict", required=True),
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
        version="v2alpha1",
        plural="ciliumbgppeeringpolicies",
        kind="CiliumBGPPeeringPolicy",
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
    """Build CiliumBGPPeeringPolicy body."""
    return {
        "apiVersion": "cilium.io/v2alpha1",
        "kind": "CiliumBGPPeeringPolicy",
        "metadata": build_metadata(module, cluster_scoped=True),
        "spec": {
            "nodeSelector": module.params["node_selector"],
            "virtualRouters": module.params["virtual_routers"],
        },
    }


if __name__ == "__main__":
    main()
