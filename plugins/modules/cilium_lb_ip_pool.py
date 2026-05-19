# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumLoadBalancerIPPool resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_lb_ip_pool
short_description: Manage CiliumLoadBalancerIPPool resources
description:
  - Create, update, or delete CiliumLoadBalancerIPPool custom resources.
  - Defines IP address pools for LoadBalancer service allocation.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumLoadBalancerIPPool resource.
    type: str
    required: true
  cidrs:
    description:
      - List of CIDR blocks to use as the IP pool.
      - Each item is a dict with a C(cidr) key.
    type: list
    elements: dict
    required: true
  service_selector:
    description:
      - Label selector to match services for this IP pool.
      - If empty, the pool is available to all LoadBalancer services.
    type: dict
  disabled:
    description:
      - Whether this pool is disabled.
    type: bool
    default: false
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Create an IP pool for LoadBalancer services
  stevefulme1.cilium.cilium_lb_ip_pool:
    name: default-pool
    cidrs:
      - cidr: 10.100.0.0/24
      - cidr: 10.100.1.0/24

- name: Create pool restricted to specific services
  stevefulme1.cilium.cilium_lb_ip_pool:
    name: web-pool
    cidrs:
      - cidr: 192.168.10.0/28
    service_selector:
      matchLabels:
        tier: frontend

- name: Delete an IP pool
  stevefulme1.cilium.cilium_lb_ip_pool:
    name: default-pool
    state: absent
"""

RETURN = r"""
resource:
  description: The CiliumLoadBalancerIPPool resource dict.
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
        cidrs=dict(type="list", elements="dict", required=True),
        service_selector=dict(type="dict"),
        disabled=dict(type="bool", default=False),
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
        plural="ciliumloadbalancerippools",
        kind="CiliumLoadBalancerIPPool",
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
    """Build CiliumLoadBalancerIPPool body."""
    spec = {
        "cidrs": module.params["cidrs"],
        "disabled": module.params["disabled"],
    }
    if module.params.get("service_selector"):
        spec["serviceSelector"] = module.params["service_selector"]

    return {
        "apiVersion": "cilium.io/v2alpha1",
        "kind": "CiliumLoadBalancerIPPool",
        "metadata": build_metadata(module, cluster_scoped=True),
        "spec": spec,
    }


if __name__ == "__main__":
    main()
