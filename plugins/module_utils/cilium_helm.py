"""Helm operations helper for Cilium Ansible modules."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import subprocess


class CiliumHelmHelper:
    """Wraps Helm CLI operations for Cilium install/upgrade/uninstall."""

    def __init__(self, module):
        self.module = module
        self.kubeconfig = module.params.get("kubeconfig")
        self.context = module.params.get("context")

    def _base_cmd(self):
        cmd = ["helm"]
        if self.kubeconfig:
            cmd.extend(["--kubeconfig", self.kubeconfig])
        if self.context:
            cmd.extend(["--kube-context", self.context])
        return cmd

    def _run(self, args, check=True):
        cmd = self._base_cmd() + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
            if check and result.returncode != 0:
                self.module.fail_json(
                    msg="Helm command failed: {0}".format(result.stderr.strip()),
                    cmd=" ".join(cmd),
                    rc=result.returncode,
                    stderr=result.stderr,
                )
            return result
        except FileNotFoundError:
            self.module.fail_json(msg="helm binary not found in PATH")
        except subprocess.TimeoutExpired:
            self.module.fail_json(msg="Helm command timed out after 600 seconds")

    def add_repo(self, name, url):
        self._run(["repo", "add", name, url, "--force-update"])
        self._run(["repo", "update"])

    def get_release(self, release, namespace):
        result = self._run(
            ["status", release, "--namespace", namespace, "--output", "json"],
            check=False,
        )
        if result.returncode != 0:
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return None

    def install(self, release, chart, namespace, values=None, version=None, wait=True, timeout="300s"):
        args = [
            "install", release, chart,
            "--namespace", namespace,
            "--create-namespace",
            "--output", "json",
        ]
        if version:
            args.extend(["--version", version])
        if wait:
            args.extend(["--wait", "--timeout", timeout])
        if values:
            for key, val in values.items():
                args.extend(["--set", "{0}={1}".format(key, val)])
        result = self._run(args)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"info": {"status": "deployed"}}

    def upgrade(self, release, chart, namespace, values=None, version=None, wait=True, timeout="300s"):
        args = [
            "upgrade", release, chart,
            "--namespace", namespace,
            "--output", "json",
        ]
        if version:
            args.extend(["--version", version])
        if wait:
            args.extend(["--wait", "--timeout", timeout])
        if values:
            for key, val in values.items():
                args.extend(["--set", "{0}={1}".format(key, val)])
        result = self._run(args)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"info": {"status": "deployed"}}

    def uninstall(self, release, namespace, wait=True):
        args = ["uninstall", release, "--namespace", namespace]
        if wait:
            args.append("--wait")
        self._run(args)

    def get_values(self, release, namespace):
        result = self._run(
            ["get", "values", release, "--namespace", namespace, "--output", "json"],
            check=False,
        )
        if result.returncode != 0:
            return {}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {}
