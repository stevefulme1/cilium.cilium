# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumNodeConfig resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_node_config
short_description: Manage CiliumNodeConfig resources
description:
  - Create, update, or delete CiliumNodeConfig custom resources.
  - Allows per-node Cilium configuration overrides.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumNodeConfig resource.
    type: str
    required: true
  node_selector:
    description:
      - Label selector to match nodes for this configuration.
    type: dict
    required: true
  defaults:
    description:
      - Configuration defaults to apply to matched nodes.
      - Keys are Cilium config option names; values are their settings.
    type: dict
    required: true
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Override config for gateway nodes
  stevefulme1.cilium.cilium_node_config:
    name: gateway-node-config
    namespace: kube-system
    node_selector:
      matchLabels:
        node-role: gateway
    defaults:
      enable-ip-masq-agent: "true"
      egress-masquerade-interfaces: eth0

- name: Configure debug logging on specific nodes
  stevefulme1.cilium.cilium_node_config:
    name: debug-nodes
    namespace: kube-system
    node_selector:
      matchLabels:
        debug: "true"
    defaults:
      debug: "true"
      debug-verbose: flow

- name: Delete node config
  stevefulme1.cilium.cilium_node_config:
    name: gateway-node-config
    namespace: kube-system
    state: absent
"""

RETURN = r"""
resource:
  description: The CiliumNodeConfig resource dict.
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
        defaults=dict(type="dict", required=True),
    )
    argument_spec.update(CILIUM_COMMON_ARGS)
    # Override namespace default
    argument_spec["namespace"]["default"] = "kube-system"

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
        plural="ciliumnodeconfigs",
        kind="CiliumNodeConfig",
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
    """Build CiliumNodeConfig body."""
    return {
        "apiVersion": "cilium.io/v2alpha1",
        "kind": "CiliumNodeConfig",
        "metadata": build_metadata(module),
        "spec": {
            "nodeSelector": module.params["node_selector"],
            "defaults": module.params["defaults"],
        },
    }


if __name__ == "__main__":
    main()
