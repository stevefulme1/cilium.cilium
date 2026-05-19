# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Ansible module for managing CiliumLocalRedirectPolicy resources."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r"""
---
module: cilium_local_redirect_policy
short_description: Manage CiliumLocalRedirectPolicy resources
description:
  - Create, update, or delete CiliumLocalRedirectPolicy custom resources.
  - Redirects traffic destined for a service to a local backend pod on the same node.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
options:
  name:
    description:
      - Name of the CiliumLocalRedirectPolicy resource.
    type: str
    required: true
  redirect_frontend:
    description:
      - Frontend service or address to redirect from.
      - Can specify a service matcher or IP/port pair.
    type: dict
    required: true
  redirect_backend:
    description:
      - Backend configuration to redirect traffic to.
      - Specifies local pods and ports to receive redirected traffic.
    type: dict
    required: true
  description:
    description:
      - Description of the redirect policy.
    type: str
extends_documentation_fragment:
  - stevefulme1.cilium.cilium_common
"""

EXAMPLES = r"""
- name: Redirect kube-dns to node-local DNS
  stevefulme1.cilium.cilium_local_redirect_policy:
    name: local-dns
    namespace: kube-system
    redirect_frontend:
      serviceMatcher:
        serviceName: kube-dns
        namespace: kube-system
    redirect_backend:
      localEndpointSelector:
        matchLabels:
          k8s-app: node-local-dns
      toPorts:
        - port: "53"
          protocol: UDP
        - port: "53"
          protocol: TCP

- name: Redirect using address matcher
  stevefulme1.cilium.cilium_local_redirect_policy:
    name: local-redirect-ip
    namespace: default
    redirect_frontend:
      addressMatcher:
        ip: 169.254.169.254
        toPorts:
          - port: "80"
            protocol: TCP
    redirect_backend:
      localEndpointSelector:
        matchLabels:
          app: metadata-proxy
      toPorts:
        - port: "8080"
          protocol: TCP

- name: Delete redirect policy
  stevefulme1.cilium.cilium_local_redirect_policy:
    name: local-dns
    namespace: kube-system
    state: absent
"""

RETURN = r"""
resource:
  description: The CiliumLocalRedirectPolicy resource dict.
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
        redirect_frontend=dict(type="dict", required=True),
        redirect_backend=dict(type="dict", required=True),
        description=dict(type="str"),
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
        plural="ciliumlocalredirectpolicies",
        kind="CiliumLocalRedirectPolicy",
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
    """Build CiliumLocalRedirectPolicy body."""
    spec = {
        "redirectFrontend": module.params["redirect_frontend"],
        "redirectBackend": module.params["redirect_backend"],
    }
    if module.params.get("description"):
        spec["description"] = module.params["description"]

    return {
        "apiVersion": "cilium.io/v2",
        "kind": "CiliumLocalRedirectPolicy",
        "metadata": build_metadata(module),
        "spec": spec,
    }


if __name__ == "__main__":
    main()
