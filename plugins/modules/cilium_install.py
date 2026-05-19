# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for deploying Cilium via Helm."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_install
short_description: Deploy Cilium via Helm
description:
  - Install Cilium CNI into a Kubernetes cluster using Helm.
  - Manages the full lifecycle including install and uninstall.
  - Supports custom Helm values for configuration.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  release_name:
    description:
      - Helm release name for Cilium.
    type: str
    default: cilium
  chart_version:
    description:
      - Version of the Cilium Helm chart to install.
    type: str
  values:
    description:
      - Dictionary of Helm values to pass to the chart.
    type: dict
    default: {}
  helm_repo_url:
    description:
      - URL of the Helm chart repository.
    type: str
    default: https://helm.cilium.io/
  chart_ref:
    description:
      - Helm chart reference.
    type: str
    default: cilium/cilium
  state:
    description:
      - Desired state of the Cilium installation.
    type: str
    choices: [present, absent]
    default: present
  namespace:
    description:
      - Kubernetes namespace for the Cilium installation.
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
  wait:
    description:
      - Whether to wait for the install to complete.
    type: bool
    default: true
  timeout:
    description:
      - Timeout for Helm operations.
    type: str
    default: "600s"
  helm_binary:
    description:
      - Path to the Helm binary.
    type: str
    default: helm
"""

EXAMPLES = r"""
- name: Install Cilium with defaults
  stevefulme1.cilium.cilium_install:
    state: present

- name: Install Cilium with specific version and custom values
  stevefulme1.cilium.cilium_install:
    chart_version: "1.15.0"
    values:
      hubble:
        enabled: true
        relay:
          enabled: true
      ipam:
        mode: kubernetes

- name: Uninstall Cilium
  stevefulme1.cilium.cilium_install:
    state: absent
"""

RETURN = r"""
release:
  description: Helm release information.
  type: dict
  returned: always
  sample:
    name: cilium
    namespace: kube-system
    status: deployed
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
        release_name=dict(type="str", default="cilium"),
        chart_version=dict(type="str"),
        values=dict(type="dict", default={}),
        helm_repo_url=dict(type="str", default="https://helm.cilium.io/"),
        chart_ref=dict(type="str", default="cilium/cilium"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        namespace=dict(type="str", default="kube-system"),
        kubeconfig=dict(type="str"),
        context=dict(type="str"),
        wait=dict(type="bool", default=True),
        timeout=dict(type="str", default="600s"),
        helm_binary=dict(type="str", default="helm"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_K8S_SDK:
        module.fail_json(msg="kubernetes Python SDK is required")

    helper = CiliumHelmHelper(module)

    state = module.params["state"]
    release_name = module.params["release_name"]
    namespace = module.params["namespace"]
    chart_ref = module.params["chart_ref"]
    chart_version = module.params["chart_version"]
    repo_url = module.params["helm_repo_url"]
    values = module.params["values"]
    wait = module.params["wait"]
    timeout = module.params["timeout"]

    existing = helper.get_release(release_name, namespace)

    if state == "absent":
        if existing is None:
            module.exit_json(changed=False, release={})
        if module.check_mode:
            module.exit_json(changed=True)
        helper.uninstall(release_name, namespace)
        module.exit_json(changed=True, release={})

    # state == present
    if existing is None:
        if module.check_mode:
            module.exit_json(changed=True, release={"name": release_name, "status": "pending-install"})
        # Add repo first
        module.run_command(
            [module.params["helm_binary"], "repo", "add", "cilium", repo_url, "--force-update"],
        )
        module.run_command(
            [module.params["helm_binary"], "repo", "update"],
        )
        helper.install(
            release_name, chart_ref, namespace,
            values=values, chart_version=chart_version,
            repo_url=None, wait=wait, timeout=timeout,
        )
        release = helper.get_release(release_name, namespace) or {}
        module.exit_json(changed=True, release=release)

    # Already installed - check if values changed
    current_values = helper.get_release_values(release_name, namespace)
    if values and helper.values_changed(current_values, values):
        if module.check_mode:
            module.exit_json(changed=True, release=existing)
        helper.upgrade(
            release_name, chart_ref, namespace,
            values=values, chart_version=chart_version,
            wait=wait, timeout=timeout,
        )
        release = helper.get_release(release_name, namespace) or {}
        module.exit_json(changed=True, release=release)

    module.exit_json(changed=False, release=existing)


if __name__ == "__main__":
    main()
