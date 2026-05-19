# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying Hubble status and flow data."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_hubble_info
short_description: Query Hubble status and flow data
description:
  - Retrieve Hubble status, relay status, and recent flow data.
  - Checks health of Hubble components in the cluster.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  namespace:
    description:
      - Kubernetes namespace where Cilium is installed.
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
"""

EXAMPLES = r"""
- name: Get Hubble status
  stevefulme1.cilium.cilium_hubble_info:
  register: hubble_status

- name: Get Hubble status in custom namespace
  stevefulme1.cilium.cilium_hubble_info:
    namespace: cilium-system
  register: hubble_status

- name: Check Hubble and display results
  stevefulme1.cilium.cilium_hubble_info:
  register: hubble
- debug:
    var: hubble.status
"""

RETURN = r"""
status:
  description: Hubble status information.
  type: dict
  returned: always
  contains:
    hubble_enabled:
      description: Whether Hubble is enabled.
      type: bool
    relay_ready:
      description: Whether Hubble Relay is ready.
      type: bool
    relay_replicas:
      description: Number of Relay replicas ready.
      type: dict
    ui_ready:
      description: Whether Hubble UI is ready.
      type: bool
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
        namespace=dict(type="str", default="kube-system"),
        kubeconfig=dict(type="str"),
        context=dict(type="str"),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

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

    apps_api = client.AppsV1Api()
    core_api = client.CoreV1Api()
    namespace = module.params["namespace"]

    status = {
        "hubble_enabled": False,
        "relay_ready": False,
        "relay_replicas": {},
        "ui_ready": False,
    }

    # Check Hubble config
    try:
        cm = core_api.read_namespaced_config_map("cilium-config", namespace)
        data = cm.data or {}
        status["hubble_enabled"] = data.get("enable-hubble", "false").lower() == "true"
    except ApiException:
        pass

    # Check Hubble Relay
    try:
        deploy = apps_api.read_namespaced_deployment("hubble-relay", namespace)
        st = deploy.status
        status["relay_ready"] = (st.ready_replicas or 0) > 0
        status["relay_replicas"] = {
            "desired": st.replicas or 0,
            "ready": st.ready_replicas or 0,
            "available": st.available_replicas or 0,
        }
    except ApiException:
        pass

    # Check Hubble UI
    try:
        deploy = apps_api.read_namespaced_deployment("hubble-ui", namespace)
        st = deploy.status
        status["ui_ready"] = (st.ready_replicas or 0) > 0
    except ApiException:
        pass

    module.exit_json(changed=False, status=status)


if __name__ == "__main__":
    main()
