"""Unit tests for cilium_connectivity_test."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock


class TestCreate:
    def test_create_returns_resource(self):
        client = MagicMock()
        client.create.return_value = dict(
            metadata=dict(name="test-connectivity"),
            spec={},
        )
        result = client.create("cilium_connectivity_test", dict(name="test-connectivity"))
        assert result["metadata"]["name"] == "test-connectivity"

    def test_create_idempotent(self):
        client = MagicMock()
        client.get.return_value = dict(
            metadata=dict(name="test-connectivity"),
            spec={},
        )
        result = client.get("cilium_connectivity_test", "test-connectivity")
        assert result is not None
        assert result["metadata"]["name"] == "test-connectivity"

    def test_create_with_namespace(self):
        client = MagicMock()
        client.create.return_value = dict(
            metadata=dict(name="test-connectivity", namespace="kube-system"),
            spec={},
        )
        result = client.create("cilium_connectivity_test", dict(name="test-connectivity", namespace="kube-system"))
        assert result["metadata"]["namespace"] == "kube-system"

    def test_create_check_mode(self):
        client = MagicMock()
        client.check_mode = True
        client.create.return_value = None
        result = client.create("cilium_connectivity_test", dict(name="test-connectivity"))
        assert result is None


class TestDelete:
    def test_delete_existing(self):
        client = MagicMock()
        client.delete("cilium_connectivity_test", "test-connectivity")
        client.delete.assert_called_once_with("cilium_connectivity_test", "test-connectivity")

    def test_delete_not_found(self):
        client = MagicMock()
        client.get.return_value = None
        result = client.get("cilium_connectivity_test", "nonexistent")
        assert result is None

    def test_delete_with_namespace(self):
        client = MagicMock()
        client.delete("cilium_connectivity_test", "test-connectivity", namespace="default")
        client.delete.assert_called_once()

    def test_delete_idempotent(self):
        client = MagicMock()
        client.delete.return_value = dict(changed=False)
        result = client.delete("cilium_connectivity_test", "already-gone")
        assert result["changed"] is False


class TestList:
    def test_list_returns_items(self):
        client = MagicMock()
        client.list.return_value = [
            dict(metadata=dict(name="item-1")),
            dict(metadata=dict(name="item-2")),
        ]
        result = client.list("cilium_connectivity_test")
        assert len(result) == 2

    def test_list_empty(self):
        client = MagicMock()
        client.list.return_value = []
        result = client.list("cilium_connectivity_test")
        assert len(result) == 0

    def test_list_filtered_by_namespace(self):
        client = MagicMock()
        client.list.return_value = [dict(metadata=dict(name="item-1", namespace="test"))]
        result = client.list("cilium_connectivity_test", namespace="test")
        assert len(result) == 1
        assert result[0]["metadata"]["namespace"] == "test"

    def test_list_with_label_selector(self):
        client = MagicMock()
        client.list.return_value = [dict(metadata=dict(name="labeled", labels=dict(app="cilium")))]
        result = client.list("cilium_connectivity_test", label_selector="app=cilium")
        assert len(result) == 1


class TestGet:
    def test_get_existing(self):
        client = MagicMock()
        client.get.return_value = dict(
            metadata=dict(name="test-connectivity"),
            spec=dict(description="test resource"),
        )
        result = client.get("cilium_connectivity_test", "test-connectivity")
        assert result["metadata"]["name"] == "test-connectivity"

    def test_get_not_found_returns_none(self):
        client = MagicMock()
        client.get.return_value = None
        result = client.get("cilium_connectivity_test", "missing")
        assert result is None

    def test_get_with_namespace(self):
        client = MagicMock()
        client.get.return_value = dict(
            metadata=dict(name="test-connectivity", namespace="kube-system"),
        )
        result = client.get("cilium_connectivity_test", "test-connectivity", namespace="kube-system")
        assert result["metadata"]["namespace"] == "kube-system"


class TestUpdate:
    def test_update_returns_modified_resource(self):
        client = MagicMock()
        client.update.return_value = dict(
            metadata=dict(name="test-connectivity"),
            spec=dict(updated=True),
        )
        result = client.update("cilium_connectivity_test", "test-connectivity", dict(updated=True))
        assert result["spec"]["updated"] is True

    def test_update_preserves_name(self):
        client = MagicMock()
        client.update.return_value = dict(
            metadata=dict(name="test-connectivity"),
            spec=dict(new_field="value"),
        )
        result = client.update("cilium_connectivity_test", "test-connectivity", dict(new_field="value"))
        assert result["metadata"]["name"] == "test-connectivity"

    def test_update_idempotent(self):
        client = MagicMock()
        client.update.return_value = dict(
            metadata=dict(name="test-connectivity"),
            changed=False,
        )
        result = client.update("cilium_connectivity_test", "test-connectivity", {})
        assert result.get("changed") is False
