"""gRPC clients for Hubble Relay and Tetragon APIs."""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

try:
    import grpc
    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False

HUBBLE_DEFAULT_ENDPOINT = "hubble-relay.kube-system.svc.cluster.local:4245"
TETRAGON_DEFAULT_ENDPOINT = "localhost:54321"


class HubbleClient:
    """Connect to Hubble Relay gRPC endpoint for flow observation."""

    def __init__(self, endpoint=None, tls_enabled=False, ca_cert=None):
        self.endpoint = endpoint or HUBBLE_DEFAULT_ENDPOINT
        self.tls_enabled = tls_enabled
        self.ca_cert = ca_cert
        self._channel = None

    def connect(self):
        if not HAS_GRPC:
            raise ImportError("grpcio is required for Hubble gRPC client")
        if self.tls_enabled and self.ca_cert:
            credentials = grpc.ssl_channel_credentials(
                root_certificates=open(self.ca_cert, "rb").read(),
            )
            self._channel = grpc.secure_channel(self.endpoint, credentials)
        else:
            self._channel = grpc.insecure_channel(self.endpoint)
        return self

    def close(self):
        if self._channel:
            self._channel.close()
            self._channel = None

    def get_flows(self, namespace=None, verdict=None, limit=100):
        """Query recent flows from Hubble Relay.

        Returns a list of flow dicts. In production this would use the
        Hubble observer.proto gRPC service; this implementation provides
        a compatible interface stub.
        """
        return []

    def get_status(self):
        """Query Hubble Relay server status."""
        return {"state": "unknown"}

    def get_service_map(self, namespace=None):
        """Query Hubble service dependency map."""
        return {"services": []}


class TetragonClient:
    """Connect to Tetragon gRPC endpoint for security events."""

    def __init__(self, endpoint=None, tls_enabled=False, ca_cert=None):
        self.endpoint = endpoint or TETRAGON_DEFAULT_ENDPOINT
        self.tls_enabled = tls_enabled
        self.ca_cert = ca_cert
        self._channel = None

    def connect(self):
        if not HAS_GRPC:
            raise ImportError("grpcio is required for Tetragon gRPC client")
        if self.tls_enabled and self.ca_cert:
            credentials = grpc.ssl_channel_credentials(
                root_certificates=open(self.ca_cert, "rb").read(),
            )
            self._channel = grpc.secure_channel(self.endpoint, credentials)
        else:
            self._channel = grpc.insecure_channel(self.endpoint)
        return self

    def close(self):
        if self._channel:
            self._channel.close()
            self._channel = None

    def get_events(self, event_types=None, namespace=None, limit=100):
        """Query recent events from Tetragon.

        Returns a list of event dicts. In production this would use the
        Tetragon tetragon.proto gRPC service; this implementation provides
        a compatible interface stub.
        """
        return []

    def get_status(self):
        """Query Tetragon server status."""
        return {"state": "unknown"}
