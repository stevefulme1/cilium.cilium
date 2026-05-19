# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Shared argument specs and helpers for Cilium modules."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


CILIUM_COMMON_ARGS = dict(
    state=dict(type="str", choices=["present", "absent"], default="present"),
    namespace=dict(type="str", default="default"),
    kubeconfig=dict(type="str"),
    context=dict(type="str"),
    labels=dict(type="dict"),
    annotations=dict(type="dict"),
)

CILIUM_INFO_ARGS = dict(
    name=dict(type="str"),
    namespace=dict(type="str", default="default"),
    label_selector=dict(type="str", default=""),
    kubeconfig=dict(type="str"),
    context=dict(type="str"),
)


def to_dict(obj):
    """Convert a Kubernetes API object to a plain dict."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return dict(obj)


def build_metadata(module, cluster_scoped=False):
    """Build metadata dict from standard params."""
    meta = {"name": module.params["name"]}
    if not cluster_scoped and module.params.get("namespace"):
        meta["namespace"] = module.params["namespace"]
    if module.params.get("labels"):
        meta["labels"] = module.params["labels"]
    if module.params.get("annotations"):
        meta["annotations"] = module.params["annotations"]
    return meta


def filter_none(d):
    """Remove None values from a dict recursively."""
    if not isinstance(d, dict):
        return d
    return {k: filter_none(v) for k, v in d.items() if v is not None}
