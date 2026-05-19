# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying CiliumIdentity resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_identity_info
short_description: Query CiliumIdentity resources
description:
  - Retrieve information about CiliumIdentity custom resources.
  - CiliumIdentities represent security identities assigned to endpoints.
  - Cluster-scoped resource.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name (numeric ID) of a specific CiliumIdentity to retrieve.
    type: str
  label_selector:
    description:
      - Label selector to filter identities.
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
- name: List all Cilium identities
  stevefulme1.cilium.cilium_identity_info:
  register: identities

- name: Get a specific identity by numeric ID
  stevefulme1.cilium.cilium_identity_info:
    name: "12345"
  register: identity

- name: Filter identities by label
  stevefulme1.cilium.cilium_identity_info:
    label_selector: "k8s:io.kubernetes.pod.namespace=production"
  register: prod_identities
"""

RETURN = r"""
resources:
  description: List of CiliumIdentity resources.
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
        version="v2",
        plural="ciliumidentities",
        kind="CiliumIdentity",
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
