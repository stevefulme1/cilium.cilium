"""Shared pytest fixtures for Cilium collection unit tests."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import sys
import types
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# 1.  Provide a mock ``kubernetes`` SDK if the real one is not installed.
#     This must happen before any collection code is imported so that
#     ``try: import kubernetes`` blocks see HAS_K8S_SDK = True.
# ---------------------------------------------------------------------------
try:
    import kubernetes as _real_k8s  # noqa: F401
except ImportError:
    class _ApiException(Exception):
        """Minimal stand-in for kubernetes.client.exceptions.ApiException."""
        def __init__(self, status=None, reason=None, body=None, headers=None):
            self.status = status
            self.reason = reason
            self.body = body or ""
            self.headers = headers or {}
            super().__init__(reason)

    class _ConfigException(Exception):
        """Stand-in for kubernetes.config.ConfigException."""

    # Build the ``kubernetes`` package tree
    _k8s = types.ModuleType("kubernetes")
    _k8s.__path__ = []
    _k8s.__package__ = "kubernetes"

    # kubernetes.client
    _k8s_client = MagicMock()
    _k8s_client.ApiException = _ApiException
    _k8s_client.CustomObjectsApi = MagicMock
    _k8s_client.CoreV1Api = MagicMock
    _k8s_client.AppsV1Api = MagicMock
    _k8s_client.ApiClient = MagicMock
    _k8s_client.Configuration = MagicMock
    _k8s.client = _k8s_client

    # kubernetes.client.exceptions
    _k8s_client_exceptions = types.ModuleType("kubernetes.client.exceptions")
    _k8s_client_exceptions.ApiException = _ApiException
    _k8s_client.exceptions = _k8s_client_exceptions

    # kubernetes.config
    _k8s_config = MagicMock()
    _k8s_config.ConfigException = _ConfigException
    _k8s_config.load_kube_config = MagicMock()
    _k8s_config.load_incluster_config = MagicMock()
    _k8s.config = _k8s_config

    # kubernetes.dynamic
    _k8s_dynamic = types.ModuleType("kubernetes.dynamic")
    _k8s_dynamic.__path__ = []
    _k8s_dynamic.DynamicClient = MagicMock
    _k8s.dynamic = _k8s_dynamic

    # kubernetes.stream
    _k8s_stream = types.ModuleType("kubernetes.stream")
    _k8s_stream.__path__ = []
    _k8s_stream.stream = MagicMock()
    _k8s.stream = _k8s_stream

    for _name, _mod in [
        ("kubernetes", _k8s),
        ("kubernetes.client", _k8s_client),
        ("kubernetes.client.exceptions", _k8s_client_exceptions),
        ("kubernetes.config", _k8s_config),
        ("kubernetes.dynamic", _k8s_dynamic),
        ("kubernetes.stream", _k8s_stream),
    ]:
        sys.modules[_name] = _mod


# ---------------------------------------------------------------------------
# 2.  Provide a mock ``grpc`` module for EDA event source tests.
# ---------------------------------------------------------------------------
try:
    import grpc as _real_grpc  # noqa: F401
except ImportError:
    _grpc = MagicMock()
    _grpc.__path__ = []
    _grpc_aio = MagicMock()
    _grpc.aio = _grpc_aio

    sys.modules["grpc"] = _grpc
    sys.modules["grpc.aio"] = _grpc_aio


# ---------------------------------------------------------------------------
# 3.  Set up the ansible_collections.stevefulme1.cilium namespace package
#     so that collection imports work from a standalone checkout or CI.
# ---------------------------------------------------------------------------
_collection_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

# When the repo is checked out inside an ansible_collections/stevefulme1/cilium/
# directory tree (e.g. CI), the grandparent provides the namespace package.
_namespace_root = os.path.abspath(os.path.join(_collection_root, os.pardir, os.pardir))
if os.path.isdir(os.path.join(_namespace_root, "ansible_collections")) and _namespace_root not in sys.path:
    sys.path.insert(0, _namespace_root)

# Try importing; if it fails, build the namespace synthetically.
try:
    import ansible_collections.stevefulme1.cilium  # noqa: F401
except (ImportError, ModuleNotFoundError):
    for _pkg_name in ("ansible_collections", "ansible_collections.stevefulme1"):
        if _pkg_name not in sys.modules:
            _pkg = types.ModuleType(_pkg_name)
            _pkg.__path__ = []
            _pkg.__package__ = _pkg_name
            sys.modules[_pkg_name] = _pkg

    _cilium_mod = types.ModuleType("ansible_collections.stevefulme1.cilium")
    _cilium_mod.__path__ = [_collection_root]
    _cilium_mod.__package__ = "ansible_collections.stevefulme1.cilium"
    sys.modules["ansible_collections.stevefulme1.cilium"] = _cilium_mod

    sys.modules["ansible_collections"].stevefulme1 = sys.modules["ansible_collections.stevefulme1"]
    sys.modules["ansible_collections.stevefulme1"].cilium = _cilium_mod


@pytest.fixture
def module_args():
    """Return a base dict of Kubernetes common module arguments."""
    return {
        "kubeconfig": "~/.kube/config",
        "context": "default",
        "namespace": "kube-system",
        "wait": True,
        "wait_timeout": 300,
        "wait_interval": 10,
        "state": "present",
    }


@pytest.fixture
def mock_k8s_client():
    """Factory fixture that returns a MagicMock configured as a Kubernetes API client.

    Usage in tests:
        def test_something(mock_k8s_client):
            client = mock_k8s_client("CustomObjectsApi")
            client.get_namespaced_custom_object.return_value = ...
    """
    def _factory(client_name: str = "CustomObjectsApi") -> MagicMock:
        client = MagicMock(name=client_name)
        return client

    return _factory


@pytest.fixture
def mock_custom_objects_api():
    """Pre-built CustomObjectsApi mock with common methods."""
    api = MagicMock(name="CustomObjectsApi")
    api.create_namespaced_custom_object = MagicMock()
    api.get_namespaced_custom_object = MagicMock()
    api.patch_namespaced_custom_object = MagicMock()
    api.delete_namespaced_custom_object = MagicMock()
    api.list_namespaced_custom_object = MagicMock()
    api.create_cluster_custom_object = MagicMock()
    api.get_cluster_custom_object = MagicMock()
    api.patch_cluster_custom_object = MagicMock()
    api.delete_cluster_custom_object = MagicMock()
    api.list_cluster_custom_object = MagicMock()
    return api
