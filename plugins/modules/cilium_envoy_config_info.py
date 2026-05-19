# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying CiliumEnvoyConfig resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_envoy_config_info
short_description: Query CiliumEnvoyConfig resources
description:
  - Retrieve information about CiliumEnvoyConfig custom resources.
  - Can query both namespaced and cluster-wide Envoy configs.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of a specific CiliumEnvoyConfig to retrieve.
    type: str
  namespace:
    description:
      - Kubernetes namespace to query.
      - Set to empty string for cluster-wide configs.
    type: str
    default: default
  label_selector:
    description:
      - Label selector to filter resources.
    type: str
    default: ""
  cluster_wide:
    description:
      - Whether to query CiliumClusterwideEnvoyConfig resources instead.
    type: bool
    default: false
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
- name: List all CiliumEnvoyConfigs in a namespace
  stevefulme1.cilium.cilium_envoy_config_info:
    namespace: production
  register: envoy_configs

- name: Get a specific Envoy config
  stevefulme1.cilium.cilium_envoy_config_info:
    name: envoy-lb
    namespace: production
  register: envoy_config

- name: List all cluster-wide Envoy configs
  stevefulme1.cilium.cilium_envoy_config_info:
    cluster_wide: true
  register: cw_envoy_configs
"""

RETURN = r"""
resources:
  description: List of CiliumEnvoyConfig or CiliumClusterwideEnvoyConfig resources.
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
    CILIUM_INFO_ARGS,
    to_dict,
)
from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_k8s import CiliumCrdHelper


def main():
    argument_spec = dict(CILIUM_INFO_ARGS)
    argument_spec["cluster_wide"] = dict(type="bool", default=False)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_K8S_SDK:
        module.fail_json(msg="kubernetes Python SDK is required")

    cluster_wide = module.params["cluster_wide"]
    if cluster_wide:
        plural = "ciliumclusterwideenvoyconfigs"
        kind = "CiliumClusterwideEnvoyConfig"
    else:
        plural = "ciliumenvoyconfigs"
        kind = "CiliumEnvoyConfig"

    helper = CiliumCrdHelper(
        module,
        group="cilium.io",
        version="v2",
        plural=plural,
        kind=kind,
        cluster_scoped=cluster_wide,
    )

    name = module.params.get("name")
    namespace = module.params["namespace"]
    label_selector = module.params.get("label_selector", "")

    if name:
        if cluster_wide:
            result = helper.get(name)
        else:
            result = helper.get(name, namespace)
        if result is None:
            module.exit_json(changed=False, resources=[])
        module.exit_json(changed=False, resources=[to_dict(result)])
    else:
        if cluster_wide:
            results = helper.list(label_selector=label_selector)
        else:
            results = helper.list(namespace, label_selector=label_selector)
        module.exit_json(changed=False, resources=[to_dict(r) for r in results])


if __name__ == "__main__":
    main()
