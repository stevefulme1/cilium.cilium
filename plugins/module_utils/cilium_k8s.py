# -*- coding: utf-8 -*-
# Copyright (c) 2025, Steve Fulmer
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Kubernetes CRD and Helm helpers for Cilium modules."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import copy
import json
import os
import subprocess

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    HAS_K8S_SDK = True
except ImportError:
    HAS_K8S_SDK = False


class CiliumK8sClient(object):
    """Base Kubernetes client wrapper."""

    def __init__(self, module):
        self.module = module
        kubeconfig = module.params.get("kubeconfig")
        context = module.params.get("context")
        try:
            if kubeconfig:
                config.load_kube_config(
                    config_file=kubeconfig, context=context
                )
            else:
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config(context=context)
        except Exception as e:
            module.fail_json(msg="Failed to load kubeconfig: %s" % str(e))

        self.api = client.CustomObjectsApi()
        self.core_api = client.CoreV1Api()
        self.apps_api = client.AppsV1Api()


class CiliumCrdHelper(CiliumK8sClient):
    """Helper for managing Cilium CRDs."""

    def __init__(self, module, group, version, plural, kind,
                 cluster_scoped=False):
        super(CiliumCrdHelper, self).__init__(module)
        self.group = group
        self.version = version
        self.plural = plural
        self.kind = kind
        self.cluster_scoped = cluster_scoped

    def get(self, name, namespace=None):
        """Get a single CRD object."""
        try:
            if self.cluster_scoped:
                return self.api.get_cluster_custom_object(
                    self.group, self.version, self.plural, name
                )
            return self.api.get_namespaced_custom_object(
                self.group, self.version, namespace or "default",
                self.plural, name
            )
        except ApiException as e:
            if e.status == 404:
                return None
            self.module.fail_json(
                msg="Failed to get %s/%s: %s" % (self.kind, name, str(e))
            )

    def list(self, namespace=None, label_selector=""):
        """List CRD objects."""
        try:
            if self.cluster_scoped:
                result = self.api.list_cluster_custom_object(
                    self.group, self.version, self.plural,
                    label_selector=label_selector,
                )
            else:
                result = self.api.list_namespaced_custom_object(
                    self.group, self.version, namespace or "default",
                    self.plural, label_selector=label_selector,
                )
            return result.get("items", [])
        except ApiException as e:
            self.module.fail_json(
                msg="Failed to list %s: %s" % (self.plural, str(e))
            )

    def create(self, body):
        """Create a CRD object."""
        try:
            if self.cluster_scoped:
                return self.api.create_cluster_custom_object(
                    self.group, self.version, self.plural, body
                )
            ns = body.get("metadata", {}).get("namespace", "default")
            return self.api.create_namespaced_custom_object(
                self.group, self.version, ns, self.plural, body
            )
        except ApiException as e:
            self.module.fail_json(
                msg="Failed to create %s: %s" % (self.kind, str(e))
            )

    def update(self, name, body, namespace=None):
        """Replace (update) a CRD object."""
        try:
            if self.cluster_scoped:
                return self.api.replace_cluster_custom_object(
                    self.group, self.version, self.plural, name, body
                )
            return self.api.replace_namespaced_custom_object(
                self.group, self.version, namespace or "default",
                self.plural, name, body
            )
        except ApiException as e:
            self.module.fail_json(
                msg="Failed to update %s/%s: %s" % (
                    self.kind, name, str(e))
            )

    def delete(self, name, namespace=None):
        """Delete a CRD object."""
        try:
            if self.cluster_scoped:
                return self.api.delete_cluster_custom_object(
                    self.group, self.version, self.plural, name
                )
            return self.api.delete_namespaced_custom_object(
                self.group, self.version, namespace or "default",
                self.plural, name
            )
        except ApiException as e:
            self.module.fail_json(
                msg="Failed to delete %s/%s: %s" % (
                    self.kind, name, str(e))
            )

    def needs_update(self, existing, desired):
        """Check if the existing resource differs from the desired state."""
        existing_spec = existing.get("spec", {})
        desired_spec = desired.get("spec", {})
        existing_labels = existing.get("metadata", {}).get("labels", {})
        desired_labels = desired.get("metadata", {}).get("labels", {})
        existing_annot = existing.get("metadata", {}).get("annotations", {})
        desired_annot = desired.get("metadata", {}).get("annotations", {})

        if desired_labels and desired_labels != existing_labels:
            return True
        if desired_annot and desired_annot != existing_annot:
            return True
        return json.dumps(existing_spec, sort_keys=True) != json.dumps(
            desired_spec, sort_keys=True
        )


class CiliumHelmHelper(CiliumK8sClient):
    """Helper for managing Cilium via Helm."""

    def __init__(self, module):
        super(CiliumHelmHelper, self).__init__(module)
        self.helm_bin = module.params.get("helm_binary", "helm")

    def _run_helm(self, args, check_rc=True):
        """Run a helm command and return stdout."""
        cmd = [self.helm_bin] + args
        kubeconfig = self.module.params.get("kubeconfig")
        context = self.module.params.get("context")
        if kubeconfig:
            cmd.extend(["--kubeconfig", kubeconfig])
        if context:
            cmd.extend(["--kube-context", context])

        rc, stdout, stderr = self.module.run_command(cmd)
        if check_rc and rc != 0:
            self.module.fail_json(
                msg="Helm command failed: %s" % stderr, cmd=" ".join(cmd)
            )
        return rc, stdout, stderr

    def get_release(self, release_name, namespace):
        """Get current Helm release info."""
        rc, stdout, stderr = self._run_helm(
            ["status", release_name, "-n", namespace, "-o", "json"],
            check_rc=False,
        )
        if rc != 0:
            return None
        try:
            return json.loads(stdout)
        except (ValueError, TypeError):
            return None

    def get_release_values(self, release_name, namespace):
        """Get current values for a Helm release."""
        rc, stdout, stderr = self._run_helm(
            ["get", "values", release_name, "-n", namespace, "-o", "json"],
            check_rc=False,
        )
        if rc != 0:
            return {}
        try:
            return json.loads(stdout)
        except (ValueError, TypeError):
            return {}

    def install(self, release_name, chart, namespace, values=None,
                chart_version=None, repo_url=None, wait=True, timeout=None,
                extra_args=None):
        """Install a Helm chart."""
        args = ["install", release_name, chart, "-n", namespace,
                "--create-namespace"]
        if chart_version:
            args.extend(["--version", chart_version])
        if repo_url:
            args.extend(["--repo", repo_url])
        if wait:
            args.append("--wait")
        if timeout:
            args.extend(["--timeout", timeout])
        if values:
            for key, val in self._flatten_values(values).items():
                args.extend(["--set", "%s=%s" % (key, val)])
        if extra_args:
            args.extend(extra_args)
        self._run_helm(args)

    def upgrade(self, release_name, chart, namespace, values=None,
                chart_version=None, repo_url=None, wait=True, timeout=None,
                extra_args=None, reuse_values=True):
        """Upgrade a Helm release."""
        args = ["upgrade", release_name, chart, "-n", namespace]
        if chart_version:
            args.extend(["--version", chart_version])
        if repo_url:
            args.extend(["--repo", repo_url])
        if wait:
            args.append("--wait")
        if timeout:
            args.extend(["--timeout", timeout])
        if reuse_values:
            args.append("--reuse-values")
        if values:
            for key, val in self._flatten_values(values).items():
                args.extend(["--set", "%s=%s" % (key, val)])
        if extra_args:
            args.extend(extra_args)
        self._run_helm(args)

    def uninstall(self, release_name, namespace):
        """Uninstall a Helm release."""
        self._run_helm(["uninstall", release_name, "-n", namespace])

    def _flatten_values(self, values, parent_key="", sep="."):
        """Flatten nested dict to dot-notation for --set."""
        items = {}
        if not isinstance(values, dict):
            return items
        for k, v in values.items():
            new_key = "%s%s%s" % (parent_key, sep, k) if parent_key else k
            if isinstance(v, dict):
                items.update(self._flatten_values(v, new_key, sep))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    idx_key = "%s[%d]" % (new_key, i)
                    if isinstance(item, dict):
                        items.update(self._flatten_values(item, idx_key, sep))
                    else:
                        items[idx_key] = str(item)
            elif isinstance(v, bool):
                items[new_key] = str(v).lower()
            else:
                items[new_key] = str(v)
        return items

    def values_changed(self, current_values, desired_values):
        """Check if desired values differ from current release values."""
        if not desired_values:
            return False
        flat_current = self._flatten_values(current_values)
        flat_desired = self._flatten_values(desired_values)
        for key, val in flat_desired.items():
            if flat_current.get(key) != val:
                return True
        return False
