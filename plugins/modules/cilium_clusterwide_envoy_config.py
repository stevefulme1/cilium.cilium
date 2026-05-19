# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumClusterwideEnvoyConfig resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_clusterwide_envoy_config
short_description: Manage CiliumClusterwideEnvoyConfig resources
description:
  - Create, update, or delete CiliumClusterwideEnvoyConfig custom resources.
  - Cluster-scoped Envoy proxy configuration that applies globally.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumClusterwideEnvoyConfig resource.
    type: str
    required: true
  services:
    description:
      - List of Kubernetes services whose traffic is processed by this config.
    type: list
    elements: dict
  resources:
    description:
      - List of Envoy xDS resources.
    type: list
    elements: dict
  backendServices:
    description:
      - List of backend services for traffic routing.
    type: list
    elements: dict
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Create cluster-wide Envoy config for mTLS
  stevefulme1.cilium.cilium_clusterwide_envoy_config:
    name: cluster-mtls
    resources:
      - "@type": type.googleapis.com/envoy.config.listener.v3.Listener
        name: mtls-listener

- name: Create cluster-wide L7 proxy config
  stevefulme1.cilium.cilium_clusterwide_envoy_config:
    name: cluster-l7-proxy
    services:
      - name: ingress-service
        namespace: ingress
    resources:
      - "@type": type.googleapis.com/envoy.config.listener.v3.Listener
        name: l7-proxy-listener

- name: Delete cluster-wide Envoy config
  stevefulme1.cilium.cilium_clusterwide_envoy_config:
    name: cluster-mtls
    state: absent
"""

RETURN = r"""
resource:
  description: The CiliumClusterwideEnvoyConfig resource dict.
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
        services=dict(type="list", elements="dict"),
        resources=dict(type="list", elements="dict"),
        backendServices=dict(type="list", elements="dict"),
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
        version="v2",
        plural="ciliumclusterwideenvoyconfigs",
        kind="CiliumClusterwideEnvoyConfig",
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
    """Build CiliumClusterwideEnvoyConfig body."""
    spec = {}
    if module.params.get("services"):
        spec["services"] = module.params["services"]
    if module.params.get("resources"):
        spec["resources"] = module.params["resources"]
    if module.params.get("backendServices"):
        spec["backendServices"] = module.params["backendServices"]

    return {
        "apiVersion": "cilium.io/v2",
        "kind": "CiliumClusterwideEnvoyConfig",
        "metadata": build_metadata(module, cluster_scoped=True),
        "spec": spec,
    }


if __name__ == "__main__":
    main()
