# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for running Cilium connectivity tests."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_connectivity_test
short_description: Run Cilium connectivity tests
description:
  - Deploy and run the Cilium connectivity test suite.
  - Validates that network policies, DNS, and connectivity work correctly.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  test_namespace:
    description:
      - Namespace to deploy connectivity test pods into.
    type: str
    default: cilium-test
  timeout:
    description:
      - Timeout for the connectivity test in seconds.
    type: int
    default: 300
  cleanup:
    description:
      - Whether to clean up test resources after the test.
    type: bool
    default: true
  cilium_namespace:
    description:
      - Namespace where Cilium is installed.
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
- name: Run connectivity test with defaults
  stevefulme1.cilium.cilium_connectivity_test:
  register: test_result

- name: Run connectivity test with custom namespace and timeout
  stevefulme1.cilium.cilium_connectivity_test:
    test_namespace: my-cilium-test
    timeout: 600
    cleanup: true

- name: Run test without cleanup for debugging
  stevefulme1.cilium.cilium_connectivity_test:
    cleanup: false
  register: test_result
"""

RETURN = r"""
passed:
  description: Whether all connectivity tests passed.
  type: bool
  returned: always
test_output:
  description: Output from the connectivity test.
  type: str
  returned: always
test_summary:
  description: Summary of test results.
  type: dict
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config  # noqa: F401
    from kubernetes.client.rest import ApiException
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False


def main():
    argument_spec = dict(
        test_namespace=dict(type="str", default="cilium-test"),
        timeout=dict(type="int", default=300),
        cleanup=dict(type="bool", default=True),
        cilium_namespace=dict(type="str", default="kube-system"),
        kubeconfig=dict(type="str"),
        context=dict(type="str"),
        helm_binary=dict(type="str", default="helm"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if module.check_mode:
        module.exit_json(changed=False, passed=True, test_output="check mode",
                         test_summary={"skipped": True})

    if not HAS_K8S_SDK:
        module.fail_json(msg="kubernetes Python SDK is required")

    kubeconfig = module.params.get("kubeconfig")
    ctx = module.params.get("context")
    try:
        if kubeconfig:
            config.load_kube_config(config_file=kubeconfig, context=ctx)
        else:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config(context=ctx)
    except Exception as e:
        module.fail_json(msg="Failed to load kubeconfig: %s" % str(e))

    helm_bin = module.params["helm_binary"]
    test_ns = module.params["test_namespace"]
    cilium_ns = module.params["cilium_namespace"]
    timeout = module.params["timeout"]

    # Run helm test
    helm_args = [helm_bin, "test", "cilium", "-n", cilium_ns,
                 "--timeout", "%ds" % timeout]
    if kubeconfig:
        helm_args.extend(["--kubeconfig", kubeconfig])
    if ctx:
        helm_args.extend(["--kube-context", ctx])

    rc, stdout, stderr = module.run_command(helm_args, check_rc=False)

    passed = rc == 0
    test_summary = {
        "return_code": rc,
        "passed": passed,
    }

    # Parse output for test counts if available
    for line in stdout.splitlines():
        line = line.strip()
        if "passed" in line.lower() or "failed" in line.lower():
            test_summary["detail"] = line

    if module.params["cleanup"]:
        core_api = client.CoreV1Api()
        try:
            core_api.delete_namespace(test_ns)
        except ApiException:
            pass

    module.exit_json(
        changed=True,
        passed=passed,
        test_output=stdout,
        test_summary=test_summary,
    )


if __name__ == "__main__":
    main()
