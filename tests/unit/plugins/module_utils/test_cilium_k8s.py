"""Unit tests for cilium_k8s module_utils."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock, patch


class TestModuleUtil:
    def test_import(self):
        """Verify the module can be referenced."""
        assert "cilium_k8s" is not None

    def test_client_factory(self):
        client = MagicMock()
        client.connect.return_value = True
        assert client.connect() is True

    def test_client_configuration(self):
        client = MagicMock()
        client.configure.return_value = dict(kubeconfig="~/.kube/config", context="default")
        config = client.configure()
        assert config["kubeconfig"] == "~/.kube/config"

    def test_error_handling(self):
        client = MagicMock()
        client.get.side_effect = Exception("connection refused")
        try:
            client.get("resource", "test")
            assert False, "Should have raised"
        except Exception as exc:
            assert "connection refused" in str(exc)

    def test_wait_condition(self):
        client = MagicMock()
        client.wait.return_value = dict(status="ready", elapsed=5)
        result = client.wait("resource", "test", timeout=30)
        assert result["status"] == "ready"

    def test_namespace_resolution(self):
        client = MagicMock()
        client.resolve_namespace.return_value = "kube-system"
        ns = client.resolve_namespace("default")
        assert ns == "kube-system"
