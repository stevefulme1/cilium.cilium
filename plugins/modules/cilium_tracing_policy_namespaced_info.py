# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying TracingPolicyNamespaced resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_tracing_policy_namespaced_info
short_description: Query Tetragon TracingPolicyNamespaced resources
description:
  - Retrieve information about namespace-scoped TracingPolicyNamespaced resources.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of a specific TracingPolicyNamespaced to retrieve.
    type: str
  namespace:
    description:
      - Kubernetes namespace to query.
    type: str
    default: default
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
- name: List all namespaced tracing policies
  stevefulme1.cilium.cilium_tracing_policy_namespaced_info:
    namespace: production
  register: policies

- name: Get specific namespaced tracing policy
  stevefulme1.cilium.cilium_tracing_policy_namespaced_info:
    name: monitor-exec
    namespace: production
  register: policy

- name: Filter by label
  stevefulme1.cilium.cilium_tracing_policy_namespaced_info:
    namespace: production
    label_selector: "severity=high"
  register: high_severity_policies
"""

RETURN = r"""
resources:
  description: List of TracingPolicyNamespaced resources.
  type: list
  elements: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    import kubernetes  # noqa: F401
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False

from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_common import (
    CILIUM_INFO_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_k8s import CiliumCrdHelper


def main():
    module = AnsibleModule(
        argument_spec=dict(CILIUM_INFO_ARGS),
        supports_check_mode=True,
    )

    if not HAS_K8S_SDK:
        module.fail_json(msg="kubernetes Python SDK is required")

    helper = CiliumCrdHelper(
        module,
        group="cilium.io",
        version="v1alpha1",
        plural="tracingpoliciesnamespaced",
        kind="TracingPolicyNamespaced",
    )

    name = module.params.get("name")
    namespace = module.params["namespace"]
    label_selector = module.params.get("label_selector", "")

    if name:
        result = helper.get(name, namespace)
        if result is None:
            module.exit_json(changed=False, resources=[])
        module.exit_json(changed=False, resources=[to_dict(result)])
    else:
        results = helper.list(namespace, label_selector=label_selector)
        module.exit_json(changed=False, resources=[to_dict(r) for r in results])


if __name__ == "__main__":
    main()
