# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumCIDRGroup resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_cidr_group
short_description: Manage CiliumCIDRGroup resources
description:
  - Create, update, or delete CiliumCIDRGroup custom resources.
  - CIDRGroups define reusable sets of external CIDRs that can be referenced
    in CiliumNetworkPolicy rules.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumCIDRGroup resource.
    type: str
    required: true
  external_cidrs:
    description:
      - List of external CIDR blocks in the group.
    type: list
    elements: str
    required: true
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Create CIDR group for corporate network
  stevefulme1.cilium.cilium_cidr_group:
    name: corporate-networks
    external_cidrs:
      - 10.0.0.0/8
      - 172.16.0.0/12
      - 192.168.0.0/16

- name: Create CIDR group for external vendors
  stevefulme1.cilium.cilium_cidr_group:
    name: vendor-ips
    external_cidrs:
      - 203.0.113.0/24
      - 198.51.100.0/24

- name: Delete CIDR group
  stevefulme1.cilium.cilium_cidr_group:
    name: corporate-networks
    state: absent
"""

RETURN = r"""
resource:
  description: The CiliumCIDRGroup resource dict.
  type: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    import kubernetes  # noqa: F401
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
        external_cidrs=dict(type="list", elements="str", required=True),
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
        plural="ciliumcidrgroups",
        kind="CiliumCIDRGroup",
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
    """Build CiliumCIDRGroup body."""
    return {
        "apiVersion": "cilium.io/v2alpha1",
        "kind": "CiliumCIDRGroup",
        "metadata": build_metadata(module, cluster_scoped=True),
        "spec": {
            "externalCIDRs": module.params["external_cidrs"],
        },
    }


if __name__ == "__main__":
    main()
