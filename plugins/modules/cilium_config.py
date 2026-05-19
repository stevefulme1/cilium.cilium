# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing the cilium-config ConfigMap."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_config
short_description: Manage the cilium-config ConfigMap
description:
  - Create, update, or manage the cilium-config ConfigMap in the Cilium namespace.
  - This is the primary runtime configuration mechanism for Cilium.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  config_options:
    description:
      - Dictionary of Cilium configuration key-value pairs.
      - Keys correspond to Cilium ConfigMap fields.
    type: dict
    required: true
  state:
    description:
      - Desired state of the configuration.
    type: str
    choices: [present, absent]
    default: present
  namespace:
    description:
      - Namespace where cilium-config ConfigMap resides.
    type: str
    default: kube-system
  configmap_name:
    description:
      - Name of the ConfigMap.
    type: str
    default: cilium-config
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
- name: Enable Hubble in Cilium config
  stevefulme1.cilium.cilium_config:
    config_options:
      enable-hubble: "true"
      hubble-listen-address: ":4244"

- name: Configure IPAM mode
  stevefulme1.cilium.cilium_config:
    config_options:
      ipam: kubernetes
      enable-endpoint-routes: "true"
      auto-direct-node-routes: "true"

- name: Remove specific config options
  stevefulme1.cilium.cilium_config:
    config_options:
      debug: "true"
    state: absent
"""

RETURN = r"""
config:
  description: The resulting ConfigMap data after changes.
  type: dict
  returned: always
changed_keys:
  description: List of keys that were changed.
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
        config_options=dict(type="dict", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        namespace=dict(type="str", default="kube-system"),
        configmap_name=dict(type="str", default="cilium-config"),
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
    cm_name = module.params["configmap_name"]
    config_options = module.params["config_options"]
    state = module.params["state"]

    # Get existing ConfigMap
    try:
        existing_cm = core_api.read_namespaced_config_map(cm_name, namespace)
        existing_data = existing_cm.data or {}
    except ApiException as e:
        if e.status == 404:
            existing_cm = None
            existing_data = {}
        else:
            module.fail_json(msg="Failed to read ConfigMap: %s" % str(e))

    changed_keys = []
    new_data = dict(existing_data)

    if state == "present":
        for key, value in config_options.items():
            str_val = str(value)
            if existing_data.get(key) != str_val:
                changed_keys.append(key)
                new_data[key] = str_val
    else:
        for key in config_options:
            if key in new_data:
                changed_keys.append(key)
                del new_data[key]

    if not changed_keys:
        module.exit_json(changed=False, config=existing_data, changed_keys=[])

    if module.check_mode:
        module.exit_json(changed=True, config=new_data, changed_keys=changed_keys)

    body = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=cm_name, namespace=namespace),
        data=new_data,
    )

    try:
        if existing_cm:
            result = core_api.replace_namespaced_config_map(cm_name, namespace, body)
        else:
            result = core_api.create_namespaced_config_map(namespace, body)
    except ApiException as e:
        module.fail_json(msg="Failed to update ConfigMap: %s" % str(e))

    module.exit_json(changed=True, config=result.data or {}, changed_keys=changed_keys)


if __name__ == "__main__":
    main()
