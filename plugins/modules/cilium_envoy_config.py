# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumEnvoyConfig resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_envoy_config
short_description: Manage CiliumEnvoyConfig resources
description:
  - Create, update, or delete CiliumEnvoyConfig custom resources.
  - Configures Envoy proxy settings for L7 traffic processing in a namespace.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumEnvoyConfig resource.
    type: str
    required: true
  services:
    description:
      - List of Kubernetes services whose traffic is processed by this Envoy config.
    type: list
    elements: dict
  resources:
    description:
      - List of Envoy xDS resources (listeners, clusters, routes, etc.).
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
- name: Create Envoy config for L7 load balancing
  stevefulme1.cilium.cilium_envoy_config:
    name: envoy-lb
    namespace: production
    services:
      - name: my-service
        namespace: production
    resources:
      - "@type": type.googleapis.com/envoy.config.listener.v3.Listener
        name: envoy-lb-listener

- name: Create Envoy config with rate limiting
  stevefulme1.cilium.cilium_envoy_config:
    name: envoy-ratelimit
    namespace: production
    services:
      - name: api-service
        namespace: production
    resources:
      - "@type": type.googleapis.com/envoy.config.listener.v3.Listener
        name: envoy-ratelimit-listener

- name: Delete Envoy config
  stevefulme1.cilium.cilium_envoy_config:
    name: envoy-lb
    namespace: production
    state: absent
"""

RETURN = r"""
resource:
  description: The CiliumEnvoyConfig resource dict.
  type: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client as _k8s_client
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
        plural="ciliumenvoyconfigs",
        kind="CiliumEnvoyConfig",
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
    """Build CiliumEnvoyConfig body."""
    spec = {}
    if module.params.get("services"):
        spec["services"] = module.params["services"]
    if module.params.get("resources"):
        spec["resources"] = module.params["resources"]
    if module.params.get("backendServices"):
        spec["backendServices"] = module.params["backendServices"]

    return {
        "apiVersion": "cilium.io/v2",
        "kind": "CiliumEnvoyConfig",
        "metadata": build_metadata(module),
        "spec": spec,
    }


if __name__ == "__main__":
    main()
