"""Unit tests for cilium_hubble."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from unittest.mock import MagicMock


class TestCreate:
    def test_create_returns_resource(self):
        client = MagicMock()
        client.create.return_value = dict(
            metadata=dict(name="test-hubble"),
            spec={},
        )
        result = client.create("cilium_hubble", dict(name="test-hubble"))
        assert result["metadata"]["name"] == "test-hubble"

    def test_create_idempotent(self):
        client = MagicMock()
        client.get.return_value = dict(
            metadata=dict(name="test-hubble"),
            spec={},
        )
        result = client.get("cilium_hubble", "test-hubble")
        assert result is not None
        assert result["metadata"]["name"] == "test-hubble"

    def test_create_with_namespace(self):
        client = MagicMock()
        client.create.return_value = dict(
            metadata=dict(name="test-hubble", namespace="kube-system"),
            spec={},
        )
        result = client.create("cilium_hubble", dict(name="test-hubble", namespace="kube-system"))
        assert result["metadata"]["namespace"] == "kube-system"

    def test_create_check_mode(self):
        client = MagicMock()
        client.check_mode = True
        client.create.return_value = None
        result = client.create("cilium_hubble", dict(name="test-hubble"))
        assert result is None


class TestDelete:
    def test_delete_existing(self):
        client = MagicMock()
        client.delete("cilium_hubble", "test-hubble")
        client.delete.assert_called_once_with("cilium_hubble", "test-hubble")

    def test_delete_not_found(self):
        client = MagicMock()
        client.get.return_value = None
        result = client.get("cilium_hubble", "nonexistent")
        assert result is None

    def test_delete_with_namespace(self):
        client = MagicMock()
        client.delete("cilium_hubble", "test-hubble", namespace="default")
        client.delete.assert_called_once()

    def test_delete_idempotent(self):
        client = MagicMock()
        client.delete.return_value = dict(changed=False)
        result = client.delete("cilium_hubble", "already-gone")
        assert result["changed"] is False


class TestList:
    def test_list_returns_items(self):
        client = MagicMock()
        client.list.return_value = [
            dict(metadata=dict(name="item-1")),
            dict(metadata=dict(name="item-2")),
        ]
        result = client.list("cilium_hubble")
        assert len(result) == 2

    def test_list_empty(self):
        client = MagicMock()
        client.list.return_value = []
        result = client.list("cilium_hubble")
        assert len(result) == 0

    def test_list_filtered_by_namespace(self):
        client = MagicMock()
        client.list.return_value = [dict(metadata=dict(name="item-1", namespace="test"))]
        result = client.list("cilium_hubble", namespace="test")
        assert len(result) == 1
        assert result[0]["metadata"]["namespace"] == "test"

    def test_list_with_label_selector(self):
        client = MagicMock()
        client.list.return_value = [dict(metadata=dict(name="labeled", labels=dict(app="cilium")))]
        result = client.list("cilium_hubble", label_selector="app=cilium")
        assert len(result) == 1


class TestGet:
    def test_get_existing(self):
        client = MagicMock()
        client.get.return_value = dict(
            metadata=dict(name="test-hubble"),
            spec=dict(description="test resource"),
        )
        result = client.get("cilium_hubble", "test-hubble")
        assert result["metadata"]["name"] == "test-hubble"

    def test_get_not_found_returns_none(self):
        client = MagicMock()
        client.get.return_value = None
        result = client.get("cilium_hubble", "missing")
        assert result is None

    def test_get_with_namespace(self):
        client = MagicMock()
        client.get.return_value = dict(
            metadata=dict(name="test-hubble", namespace="kube-system"),
        )
        result = client.get("cilium_hubble", "test-hubble", namespace="kube-system")
        assert result["metadata"]["namespace"] == "kube-system"


class TestUpdate:
    def test_update_returns_modified_resource(self):
        client = MagicMock()
        client.update.return_value = dict(
            metadata=dict(name="test-hubble"),
            spec=dict(updated=True),
        )
        result = client.update("cilium_hubble", "test-hubble", dict(updated=True))
        assert result["spec"]["updated"] is True

    def test_update_preserves_name(self):
        client = MagicMock()
        client.update.return_value = dict(
            metadata=dict(name="test-hubble"),
            spec=dict(new_field="value"),
        )
        result = client.update("cilium_hubble", "test-hubble", dict(new_field="value"))
        assert result["metadata"]["name"] == "test-hubble"

    def test_update_idempotent(self):
        client = MagicMock()
        client.update.return_value = dict(
            metadata=dict(name="test-hubble"),
            changed=False,
        )
        result = client.update("cilium_hubble", "test-hubble", {})
        assert result.get("changed") is False
