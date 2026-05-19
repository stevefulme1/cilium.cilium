# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for configuring Cilium Prometheus metrics."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_metrics_config
short_description: Configure Cilium Prometheus metrics
description:
  - Configure which Prometheus metrics Cilium exposes via the cilium-config ConfigMap.
  - Manages metric enablement and label configuration.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  prometheus_enabled:
    description:
      - Whether Prometheus metrics endpoint is enabled.
    type: bool
    default: true
  prometheus_port:
    description:
      - Port for the Prometheus metrics endpoint.
    type: int
    default: 9962
  operator_prometheus_enabled:
    description:
      - Whether Cilium Operator Prometheus metrics are enabled.
    type: bool
    default: true
  operator_prometheus_port:
    description:
      - Port for Operator Prometheus metrics.
    type: int
    default: 9963
  hubble_metrics:
    description:
      - List of Hubble metrics to enable.
    type: list
    elements: str
  namespace:
    description:
      - Namespace where cilium-config ConfigMap resides.
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
- name: Enable Prometheus metrics with defaults
  stevefulme1.cilium.cilium_metrics_config:
    prometheus_enabled: true

- name: Configure custom metrics port and Hubble metrics
  stevefulme1.cilium.cilium_metrics_config:
    prometheus_port: 9962
    hubble_metrics:
      - dns
      - drop
      - tcp
      - flow
      - http

- name: Disable Prometheus metrics
  stevefulme1.cilium.cilium_metrics_config:
    prometheus_enabled: false
"""

RETURN = r"""
config:
  description: The resulting metrics-related ConfigMap data.
  type: dict
  returned: always
changed_keys:
  description: List of ConfigMap keys that were changed.
  type: list
  returned: always
"""

from ansible.module_utils.basic import AnsibleModule

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False


def main():
    argument_spec = dict(
        prometheus_enabled=dict(type="bool", default=True),
        prometheus_port=dict(type="int", default=9962),
        operator_prometheus_enabled=dict(type="bool", default=True),
        operator_prometheus_port=dict(type="int", default=9963),
        hubble_metrics=dict(type="list", elements="str"),
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

    core_api = client.CoreV1Api()
    namespace = module.params["namespace"]

    try:
        existing_cm = core_api.read_namespaced_config_map("cilium-config", namespace)
        existing_data = existing_cm.data or {}
    except ApiException as e:
        module.fail_json(msg="Failed to read cilium-config: %s" % str(e))

    desired = {
        "prometheus-serve-addr": ":%d" % module.params["prometheus_port"],
        "enable-metrics": str(module.params["prometheus_enabled"]).lower(),
        "operator-prometheus-serve-addr": ":%d" % module.params["operator_prometheus_port"],
    }

    if module.params.get("hubble_metrics"):
        desired["hubble-metrics"] = " ".join(module.params["hubble_metrics"])

    changed_keys = []
    new_data = dict(existing_data)
    for key, val in desired.items():
        if existing_data.get(key) != val:
            changed_keys.append(key)
            new_data[key] = val

    if not changed_keys:
        module.exit_json(changed=False, config=existing_data, changed_keys=[])

    if module.check_mode:
        module.exit_json(changed=True, config=new_data, changed_keys=changed_keys)

    body = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name="cilium-config", namespace=namespace),
        data=new_data,
    )

    try:
        result = core_api.replace_namespaced_config_map("cilium-config", namespace, body)
    except ApiException as e:
        module.fail_json(msg="Failed to update cilium-config: %s" % str(e))

    module.exit_json(changed=True, config=result.data or {}, changed_keys=changed_keys)


if __name__ == "__main__":
    main()
