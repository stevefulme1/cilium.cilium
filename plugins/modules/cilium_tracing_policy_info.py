# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying TracingPolicy resources (Tetragon)."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_tracing_policy_info
short_description: Query Tetragon TracingPolicy resources
description:
  - Retrieve information about cluster-scoped TracingPolicy custom resources.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of a specific TracingPolicy to retrieve.
    type: str
  label_selector:
    description:
      - Label selector to filter resources.
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
- name: List all tracing policies
  stevefulme1.cilium.cilium_tracing_policy_info:
  register: policies

- name: Get a specific tracing policy
  stevefulme1.cilium.cilium_tracing_policy_info:
    name: monitor-file-opens
  register: policy

- name: Filter tracing policies by label
  stevefulme1.cilium.cilium_tracing_policy_info:
    label_selector: "team=security"
  register: security_policies
"""

RETURN = r"""
resources:
  description: List of TracingPolicy resources.
  type: list
  elements: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config
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
        version="v1alpha1",
        plural="tracingpolicies",
        kind="TracingPolicy",
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
