"""Unit tests for cilium_common module_utils."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

class TestModuleUtil:
    def test_import(self):
        from ansible_collections.stevefulme1.cilium.plugins.module_utils import cilium_common
        assert hasattr(cilium_common, "CILIUM_COMMON_ARGS")

    def test_common_args_has_state(self):
        from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_common import CILIUM_COMMON_ARGS
        assert "state" in CILIUM_COMMON_ARGS

    def test_to_dict(self):
        from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_common import to_dict
        result = to_dict({"metadata": {"name": "test"}})
        assert result["metadata"]["name"] == "test"

    def test_to_dict_none(self):
        from ansible_collections.stevefulme1.cilium.plugins.module_utils.cilium_common import to_dict
        result = to_dict(None)
        assert result == {}
