# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing TracingPolicy resources (Tetragon)."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_tracing_policy
short_description: Manage Tetragon TracingPolicy resources
description:
  - Create, update, or delete TracingPolicy custom resources for Cilium Tetragon.
  - TracingPolicies define kernel-level observability rules using kprobes, tracepoints, and uprobes.
  - Cluster-scoped resource.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the TracingPolicy resource.
    type: str
    required: true
  spec:
    description:
      - Full TracingPolicy spec containing kprobes, tracepoints, uprobes, and selectors.
    type: dict
    required: true
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Monitor file opens with Tetragon
  stevefulme1.cilium.cilium_tracing_policy:
    name: monitor-file-opens
    spec:
      kprobes:
        - call: fd_install
          syscall: false
          args:
            - index: 0
              type: int
            - index: 1
              type: file
          selectors:
            - matchActions:
                - action: Post

- name: Monitor network connections
  stevefulme1.cilium.cilium_tracing_policy:
    name: monitor-connections
    spec:
      kprobes:
        - call: tcp_connect
          syscall: false
          args:
            - index: 0
              type: sock
          selectors:
            - matchActions:
                - action: Post

- name: Delete tracing policy
  stevefulme1.cilium.cilium_tracing_policy:
    name: monitor-file-opens
    state: absent
"""

RETURN = r"""
resource:
  description: The TracingPolicy resource dict.
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
        plural="tracingpolicies",
        kind="TracingPolicy",
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
    """Build TracingPolicy body."""
    return {
        "apiVersion": "cilium.io/v1alpha1",
        "kind": "TracingPolicy",
        "metadata": build_metadata(module, cluster_scoped=True),
        "spec": module.params["spec"],
    }


if __name__ == "__main__":
    main()
