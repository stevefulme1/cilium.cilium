# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for enabling and configuring Hubble."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_hubble
short_description: Enable and configure Hubble observability
description:
  - Enable or disable Hubble and its components (Relay, UI) via Helm values.
  - Manages the Hubble observability layer in Cilium.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  enabled:
    description:
      - Whether Hubble is enabled.
    type: bool
    default: true
  relay_enabled:
    description:
      - Whether Hubble Relay is enabled for gRPC access.
    type: bool
    default: true
  ui_enabled:
    description:
      - Whether Hubble UI is enabled.
    type: bool
    default: false
  metrics:
    description:
      - List of Hubble metrics to enable.
    type: list
    elements: str
    default: ["dns", "drop", "tcp", "flow", "icmp", "http"]
  release_name:
    description:
      - Helm release name for Cilium.
    type: str
    default: cilium
  namespace:
    description:
      - Namespace of the Cilium installation.
    type: str
    default: kube-system
  kubeconfig:
    description:
      - Path to a kubeconfig file.
    type: str
  context:
    description:
      - Kubernetes context to use.
    type: str
  helm_binary:
    description:
      - Path to the Helm binary.
    type: str
    default: helm
"""

EXAMPLES = r"""
- name: Enable Hubble with Relay and UI
  stevefulme1.cilium.cilium_hubble:
    enabled: true
    relay_enabled: true
    ui_enabled: true

- name: Enable Hubble with custom metrics
  stevefulme1.cilium.cilium_hubble:
    enabled: true
    metrics:
      - dns
      - drop
      - tcp
      - flow
      - http
      - "httpV2:exemplars=true;labelsContext=source_ip,source_namespace"

- name: Disable Hubble
  stevefulme1.cilium.cilium_hubble:
    enabled: false
"""

RETURN = r"""
release:
  description: Helm release information after update.
  type: dict
  returned: always
values:
  description: Hubble-related Helm values applied.
  type: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False

from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_k8s import CiliumHelmHelper


def main():
    argument_spec = dict(
        enabled=dict(type="bool", default=True),
        relay_enabled=dict(type="bool", default=True),
        ui_enabled=dict(type="bool", default=False),
        metrics=dict(type="list", elements="str",
                     default=["dns", "drop", "tcp", "flow", "icmp", "http"]),
        release_name=dict(type="str", default="cilium"),
        namespace=dict(type="str", default="kube-system"),
        kubeconfig=dict(type="str"),
        context=dict(type="str"),
        helm_binary=dict(type="str", default="helm"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_K8S_SDK:
        module.fail_json(msg="kubernetes Python SDK is required")

    helper = CiliumHelmHelper(module)

    release_name = module.params["release_name"]
    namespace = module.params["namespace"]

    existing = helper.get_release(release_name, namespace)
    if existing is None:
        module.fail_json(msg="Cilium release '%s' not found" % release_name)

    desired_values = {
        "hubble": {
            "enabled": module.params["enabled"],
            "relay": {
                "enabled": module.params["relay_enabled"],
            },
            "ui": {
                "enabled": module.params["ui_enabled"],
            },
            "metrics": {
                "enabled": module.params["metrics"],
            },
        },
    }

    current_values = helper.get_release_values(release_name, namespace)
    if not helper.values_changed(current_values, desired_values):
        module.exit_json(changed=False, release=existing, values=desired_values)

    if module.check_mode:
        module.exit_json(changed=True, release=existing, values=desired_values)

    helper.upgrade(
        release_name, "cilium/cilium", namespace,
        values=desired_values,
    )

    release = helper.get_release(release_name, namespace) or {}
    module.exit_json(changed=True, release=release, values=desired_values)


if __name__ == "__main__":
    main()
