"""Filter plugins for Cilium data transformations."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from jinja2.runtime import Undefined

DOCUMENTATION = r"""
---
name: cilium_filters
short_description: Filters for Cilium data transformations
description:
  - Provides filters for extracting and transforming Cilium-specific data
    from endpoints, policies, flows, and identities.
version_added: "1.0.0"
author:
  - Steve Fulmer (@stevefulme1)
"""


class FilterModule(object):
    """Cilium filter plugins."""

    def filters(self):
        return {
            "cilium_endpoint_status": self.endpoint_status,
            "cilium_policy_verdict": self.policy_verdict,
            "cilium_identity_labels": self.identity_labels,
            "override": self.override_filter,
        }

    @staticmethod
    def endpoint_status(endpoint):
        """Extract the status state from a CiliumEndpoint object."""
        if isinstance(endpoint, dict):
            status = endpoint.get("status", {})
            return status.get("state", "unknown")
        return "unknown"

    @staticmethod
    def policy_verdict(flow):
        """Extract the policy verdict from a Hubble flow event."""
        if isinstance(flow, dict):
            return flow.get("verdict", "UNKNOWN")
        return "UNKNOWN"

    @staticmethod
    def identity_labels(identity):
        """Extract security labels from a CiliumIdentity object."""
        if isinstance(identity, dict):
            metadata = identity.get("metadata", {})
            labels = metadata.get("labels", {})
            security_labels = identity.get("security-labels", {})
            return security_labels if security_labels else labels
        return {}

    @staticmethod
    def override_filter(hardcoded_default, override, omit):
        """Optionally override a default value with a variable."""
        if override is None:
            return omit
        elif isinstance(override, Undefined):
            return hardcoded_default
        else:
            return override
