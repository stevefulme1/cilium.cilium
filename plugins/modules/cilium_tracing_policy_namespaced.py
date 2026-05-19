# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing TracingPolicyNamespaced resources (Tetragon)."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_tracing_policy_namespaced
short_description: Manage Tetragon TracingPolicyNamespaced resources
description:
  - Create, update, or delete TracingPolicyNamespaced custom resources.
  - Namespace-scoped version of TracingPolicy for tenant isolation.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the TracingPolicyNamespaced resource.
    type: str
    required: true
  spec:
    description:
      - Full TracingPolicyNamespaced spec with kprobes, tracepoints, uprobes, and selectors.
    type: dict
    required: true
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Monitor process execution in a namespace
  stevefulme1.cilium.cilium_tracing_policy_namespaced:
    name: monitor-exec
    namespace: production
    spec:
      kprobes:
        - call: __x64_sys_execve
          syscall: true
          args:
            - index: 0
              type: string
          selectors:
            - matchActions:
                - action: Post

- name: Monitor file writes in a namespace
  stevefulme1.cilium.cilium_tracing_policy_namespaced:
    name: monitor-writes
    namespace: sensitive-data
    spec:
      kprobes:
        - call: __x64_sys_write
          syscall: true
          args:
            - index: 0
              type: fd
            - index: 2
              type: size_t
          selectors:
            - matchActions:
                - action: Post

- name: Delete namespaced tracing policy
  stevefulme1.cilium.cilium_tracing_policy_namespaced:
    name: monitor-exec
    namespace: production
    state: absent
"""

RETURN = r"""
resource:
  description: The TracingPolicyNamespaced resource dict.
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
        spec=dict(type="dict", required=True),
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
        version="v1alpha1",
        plural="tracingpoliciesnamespaced",
        kind="TracingPolicyNamespaced",
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
    """Build TracingPolicyNamespaced body."""
    return {
        "apiVersion": "cilium.io/v1alpha1",
        "kind": "TracingPolicyNamespaced",
        "metadata": build_metadata(module),
        "spec": module.params["spec"],
    }


if __name__ == "__main__":
    main()
