"""Unit tests for cilium_k8s module_utils."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock


class TestModuleUtil:
    def test_import(self):
        from ansible_collections.stevefulme1.cilium.plugins.module_utils import cilium_k8s
        assert hasattr(cilium_k8s, "CiliumCrdHelper")

    def test_crd_helper_init(self):
        module = MagicMock()
        module.params = {"kubeconfig": None, "context": None}
        from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_k8s import CiliumCrdHelper
        helper = CiliumCrdHelper(module, "cilium.io", "v2", "ciliumnetworkpolicies", "CiliumNetworkPolicy")
        assert helper.group == "cilium.io"
        assert helper.version == "v2"
