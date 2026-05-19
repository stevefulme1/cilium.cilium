# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Documentation fragment for Cilium common options."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class ModuleDocFragment(object):

    DOCUMENTATION = r"""
options:
  state:
    description:
      - Desired state of the resource.
    type: str
    choices: [present, absent]
    default: present
  namespace:
    description:
      - Kubernetes namespace for the resource.
      - Not used for cluster-scoped resources.
    type: str
    default: default
  kubeconfig:
    description:
      - Path to a kubeconfig file.
      - If not set, the C(KUBECONFIG) environment variable or default location is used.
    type: str
  context:
    description:
      - Kubernetes context to use from the kubeconfig.
    type: str
  labels:
    description:
      - Labels to apply to the resource metadata.
    type: dict
  annotations:
    description:
      - Annotations to apply to the resource metadata.
    type: dict
"""
