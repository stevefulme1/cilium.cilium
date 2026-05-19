# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for querying Cilium DaemonSet/Deployment health."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_status_info
short_description: Query Cilium health and status
description:
  - Retrieve the health status of Cilium components in the cluster.
  - Checks the Cilium DaemonSet, Operator Deployment, and optional components.
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
- name: Get Cilium status
  stevefulme1.cilium.cilium_status_info:
  register: cilium_status

- name: Get Cilium status in custom namespace
  stevefulme1.cilium.cilium_status_info:
    namespace: cilium-system
  register: cilium_status

- name: Check Cilium health and fail if not ready
  stevefulme1.cilium.cilium_status_info:
  register: status
  failed_when: not status.status.cilium_agent.ready
"""

RETURN = r"""
status:
  description: Cilium cluster status.
  type: dict
  returned: always
  contains:
    cilium_agent:
      description: Cilium agent (DaemonSet) status.
      type: dict
    cilium_operator:
      description: Cilium Operator (Deployment) status.
      type: dict
    hubble:
      description: Hubble component status.
      type: dict
    cluster_mesh:
      description: Cluster Mesh component status.
      type: dict
    version:
      description: Cilium version from the DaemonSet image tag.
      type: str
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
        "cilium_agent": _get_daemonset_status(apps_api, "cilium", namespace),
        "cilium_operator": _get_deployment_status(apps_api, "cilium-operator", namespace),
        "hubble": {
            "relay": _get_deployment_status(apps_api, "hubble-relay", namespace),
            "ui": _get_deployment_status(apps_api, "hubble-ui", namespace),
        },
        "cluster_mesh": {
            "apiserver": _get_deployment_status(apps_api, "clustermesh-apiserver", namespace),
        },
        "version": "unknown",
    }

    # Extract version from cilium DaemonSet image
    try:
        ds = apps_api.read_namespaced_daemon_set("cilium", namespace)
        for container in ds.spec.template.spec.containers:
            if container.name == "cilium-agent":
                image = container.image or ""
                if ":" in image:
                    status["version"] = image.split(":")[-1]
                break
    except ApiException:
        pass

    # Check ConfigMap for feature flags
    try:
        cm = core_api.read_namespaced_config_map("cilium-config", namespace)
        data = cm.data or {}
        status["features"] = {
            "hubble_enabled": data.get("enable-hubble", "false").lower() == "true",
            "ipam_mode": data.get("ipam", "cluster-pool"),
            "tunnel_mode": data.get("tunnel", "vxlan"),
            "kube_proxy_replacement": data.get("kube-proxy-replacement", "disabled"),
            "enable_ipv6": data.get("enable-ipv6", "false").lower() == "true",
            "enable_wireguard": data.get("enable-wireguard", "false").lower() == "true",
            "enable_bgp_control_plane": data.get("enable-bgp-control-plane", "false").lower() == "true",
        }
    except ApiException:
        status["features"] = {}

    module.exit_json(changed=False, status=status)


def _get_daemonset_status(apps_api, name, namespace):
    """Get DaemonSet status summary."""
    try:
        ds = apps_api.read_namespaced_daemon_set(name, namespace)
        st = ds.status
        desired = st.desired_number_scheduled or 0
        ready = st.number_ready or 0
        return {
            "found": True,
            "ready": desired > 0 and desired == ready,
            "desired": desired,
            "current": st.current_number_scheduled or 0,
            "ready_count": ready,
            "updated": st.updated_number_scheduled or 0,
            "available": st.number_available or 0,
            "unavailable": st.number_unavailable or 0,
        }
    except ApiException:
        return {"found": False, "ready": False}


def _get_deployment_status(apps_api, name, namespace):
    """Get Deployment status summary."""
    try:
        deploy = apps_api.read_namespaced_deployment(name, namespace)
        st = deploy.status
        desired = st.replicas or 0
        ready = st.ready_replicas or 0
        return {
            "found": True,
            "ready": desired > 0 and desired == ready,
            "desired": desired,
            "ready_count": ready,
            "available": st.available_replicas or 0,
            "unavailable": st.unavailable_replicas or 0,
        }
    except ApiException:
        return {"found": False, "ready": False}


if __name__ == "__main__":
    main()
