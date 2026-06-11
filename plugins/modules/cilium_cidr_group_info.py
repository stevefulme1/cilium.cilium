# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying CiliumCIDRGroup resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_cidr_group_info
short_description: Query CiliumCIDRGroup resources
description:
  - Retrieve information about CiliumCIDRGroup custom resources.
  - CIDR groups define reusable sets of external CIDRs for network policies.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of a specific CiliumCIDRGroup to retrieve.
      - If omitted, all CIDR groups are returned.
    type: str
  label_selector:
    description:
      - Label selector to filter CIDR groups.
    type: str
    default: ""
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
- name: List all CIDR groups
  stevefulme1.cilium.cilium_cidr_group_info:
  register: groups

- name: Get a specific CIDR group
  stevefulme1.cilium.cilium_cidr_group_info:
    name: corporate-networks
  register: group

- name: Filter CIDR groups by label
  stevefulme1.cilium.cilium_cidr_group_info:
    label_selector: "type=internal"
  register: internal_groups
"""

RETURN = r"""
resources:
  description: List of CiliumCIDRGroup resources.
  type: list
  elements: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client as _k8s_client  # noqa: F401
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False

from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_common import (
    to_dict,
)
from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_k8s import CiliumCrdHelper


def main():
    argument_spec = dict(
        name=dict(type="str"),
        label_selector=dict(type="str", default=""),
        kubeconfig=dict(type="str"),
        context=dict(type="str"),
    )

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

    name = module.params.get("name")
    label_selector = module.params.get("label_selector", "")

    if name:
        result = helper.get(name)
        if result is None:
            module.exit_json(changed=False, resources=[])
        module.exit_json(changed=False, resources=[to_dict(result)])
    else:
        results = helper.list(label_selector=label_selector)
        module.exit_json(changed=False, resources=[to_dict(r) for r in results])


if __name__ == "__main__":
    main()
