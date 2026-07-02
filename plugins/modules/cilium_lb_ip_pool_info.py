# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying CiliumLoadBalancerIPPool resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_lb_ip_pool_info
short_description: Query CiliumLoadBalancerIPPool resources
description:
  - Retrieve information about CiliumLoadBalancerIPPool custom resources.
  - IP pools define address ranges for LoadBalancer service allocation.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of a specific CiliumLoadBalancerIPPool to retrieve.
      - If omitted, all IP pools are returned.
    type: str
  label_selector:
    description:
      - Label selector to filter IP pools.
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
- name: List all LoadBalancer IP pools
  stevefulme1.cilium.cilium_lb_ip_pool_info:
  register: pools

- name: Get a specific IP pool
  stevefulme1.cilium.cilium_lb_ip_pool_info:
    name: default-pool
  register: pool

- name: Filter IP pools by label
  stevefulme1.cilium.cilium_lb_ip_pool_info:
    label_selector: "environment=production"
  register: prod_pools
"""

RETURN = r"""
resources:
  description: List of CiliumLoadBalancerIPPool resources.
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
        plural="ciliumloadbalancerippools",
        kind="CiliumLoadBalancerIPPool",
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
