# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for upgrading Cilium via Helm."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_upgrade
short_description: Upgrade Cilium via Helm
description:
  - Upgrade an existing Cilium installation to a new version.
  - Supports pre-flight checks and post-upgrade validation.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  release_name:
    description:
      - Helm release name for Cilium.
    type: str
    default: cilium
  target_version:
    description:
      - Target Cilium chart version to upgrade to.
    type: str
    required: true
  values:
    description:
      - Dictionary of Helm values to apply during upgrade.
    type: dict
    default: {}
  pre_flight_check:
    description:
      - Run pre-flight checks before upgrading.
    type: bool
    default: true
  post_upgrade_test:
    description:
      - Run connectivity tests after upgrade completes.
    type: bool
    default: false
  chart_ref:
    description:
      - Helm chart reference.
    type: str
    default: cilium/cilium
  helm_repo_url:
    description:
      - URL of the Helm chart repository.
    type: str
    default: https://helm.cilium.io/
  namespace:
    description:
      - Kubernetes namespace of the Cilium installation.
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
      - Wait for upgrade to complete.
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
- name: Upgrade Cilium to 1.15.0
  stevefulme1.cilium.cilium_upgrade:
    target_version: "1.15.0"

- name: Upgrade Cilium with custom values and post-upgrade test
  stevefulme1.cilium.cilium_upgrade:
    target_version: "1.15.0"
    values:
      hubble:
        enabled: true
    post_upgrade_test: true

- name: Upgrade without pre-flight check
  stevefulme1.cilium.cilium_upgrade:
    target_version: "1.15.0"
    pre_flight_check: false
"""

RETURN = r"""
release:
  description: Helm release information after upgrade.
  type: dict
  returned: always
previous_version:
  description: The chart version before upgrade.
  type: str
  returned: success
pre_flight:
  description: Pre-flight check results.
  type: dict
  returned: when pre_flight_check is true
"""

import json
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
        target_version=dict(type="str", required=True),
        values=dict(type="dict", default={}),
        pre_flight_check=dict(type="bool", default=True),
        post_upgrade_test=dict(type="bool", default=False),
        chart_ref=dict(type="str", default="cilium/cilium"),
        helm_repo_url=dict(type="str", default="https://helm.cilium.io/"),
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

    release_name = module.params["release_name"]
    namespace = module.params["namespace"]
    target_version = module.params["target_version"]
    chart_ref = module.params["chart_ref"]
    values = module.params["values"]
    wait = module.params["wait"]
    timeout = module.params["timeout"]
    helm_bin = module.params["helm_binary"]

    existing = helper.get_release(release_name, namespace)
    if existing is None:
        module.fail_json(msg="Cilium release '%s' not found in namespace '%s'" % (release_name, namespace))

    # Determine current version
    current_info = existing.get("info", {})
    previous_version = existing.get("chart", {}).get("metadata", {}).get("version", "unknown")

    result = dict(
        changed=False,
        release=existing,
        previous_version=previous_version,
    )

    # Pre-flight check
    if module.params["pre_flight_check"]:
        pre_flight = _run_pre_flight(module, helper, namespace)
        result["pre_flight"] = pre_flight
        if not pre_flight.get("passed", False):
            module.fail_json(msg="Pre-flight check failed", **result)

    # Check if upgrade is needed
    if previous_version == target_version:
        current_values = helper.get_release_values(release_name, namespace)
        if not values or not helper.values_changed(current_values, values):
            module.exit_json(**result)

    if module.check_mode:
        result["changed"] = True
        module.exit_json(**result)

    # Update repo
    module.run_command([helm_bin, "repo", "update"])

    # Perform upgrade
    helper.upgrade(
        release_name, chart_ref, namespace,
        values=values, chart_version=target_version,
        wait=wait, timeout=timeout,
    )

    release = helper.get_release(release_name, namespace) or {}
    result["changed"] = True
    result["release"] = release

    # Post-upgrade test
    if module.params["post_upgrade_test"]:
        test_result = _run_post_upgrade_test(module, namespace)
        result["post_upgrade_test"] = test_result

    module.exit_json(**result)


def _run_pre_flight(module, helper, namespace):
    """Run pre-flight checks."""
    checks = {"passed": True, "details": []}
    try:
        apps_api = helper.apps_api
        ds = apps_api.read_namespaced_daemon_set("cilium", namespace)
        status = ds.status
        if status.desired_number_scheduled != status.number_ready:
            checks["passed"] = False
            checks["details"].append(
                "Not all Cilium pods are ready: %d/%d" % (
                    status.number_ready, status.desired_number_scheduled)
            )
        else:
            checks["details"].append(
                "All Cilium pods ready: %d/%d" % (
                    status.number_ready, status.desired_number_scheduled)
            )
    except Exception as e:
        checks["details"].append("Could not verify Cilium DaemonSet: %s" % str(e))
    return checks


def _run_post_upgrade_test(module, namespace):
    """Run basic post-upgrade connectivity test."""
    helm_bin = module.params.get("helm_binary", "helm")
    rc, stdout, stderr = module.run_command(
        [helm_bin, "test", module.params["release_name"], "-n", namespace],
        check_rc=False,
    )
    return {"rc": rc, "stdout": stdout, "stderr": stderr, "passed": rc == 0}


if __name__ == "__main__":
    main()
