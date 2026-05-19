"""
cilium_policy_event - Stream Hubble flow events filtered for policy violations.

Connects to Hubble Relay gRPC endpoint and streams flow events with DROPPED
verdicts, indicating Cilium network policy violations. Each policy violation
event is placed on the EDA queue for rule processing.

Arguments:
    hubble_endpoint: Hubble Relay gRPC endpoint (default: localhost:4245)
    namespace_filter: Filter events by namespace (default: empty, all namespaces)
    verdict_filter: Filter by verdict type (default: DROPPED)
    reconnect_delay: Seconds to wait before reconnecting on error (default: 5)
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import asyncio
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    import grpc
    from grpc import aio as grpc_aio

    HAS_GRPC = True
except ImportError:
    HAS_GRPC = False


# Hubble observer protobuf message types
VERDICT_DROPPED = 2
VERDICT_ERROR = 3
VERDICT_AUDIT = 5

VERDICT_MAP = {
    0: "VERDICT_UNKNOWN",
    1: "FORWARDED",
    2: "DROPPED",
    3: "ERROR",
    4: "REDIRECTED",
    5: "AUDIT",
}


def _build_flow_event(flow_data):
    """Convert a Hubble flow dict into a normalized EDA event."""
    source = flow_data.get("source", {})
    destination = flow_data.get("destination", {})
    verdict_num = flow_data.get("verdict", 0)

    return {
        "event_type": "cilium_policy_violation",
        "timestamp": flow_data.get("time", datetime.now(timezone.utc).isoformat()),
        "verdict": VERDICT_MAP.get(verdict_num, "UNKNOWN"),
        "drop_reason": flow_data.get("drop_reason", 0),
        "drop_reason_desc": flow_data.get("drop_reason_desc", ""),
        "source": {
            "namespace": source.get("namespace", ""),
            "pod_name": source.get("pod_name", ""),
            "labels": source.get("labels", []),
            "identity": source.get("identity", 0),
        },
        "destination": {
            "namespace": destination.get("namespace", ""),
            "pod_name": destination.get("pod_name", ""),
            "labels": destination.get("labels", []),
            "identity": destination.get("identity", 0),
            "port": destination.get("port", 0),
        },
        "ip": {
            "source": flow_data.get("IP", {}).get("source", ""),
            "destination": flow_data.get("IP", {}).get("destination", ""),
        },
        "l4": flow_data.get("l4", {}),
        "l7": flow_data.get("l7", {}),
        "traffic_direction": flow_data.get("traffic_direction", ""),
        "policy_match_type": flow_data.get("policy_match_type", 0),
        "node_name": flow_data.get("node_name", ""),
        "is_reply": flow_data.get("is_reply", False),
    }


async def _stream_hubble_flows(queue, endpoint, namespace_filter, verdict_filter, reconnect_delay):
    """Stream flows from Hubble Relay using gRPC."""
    verdict_values = []
    if verdict_filter:
        filter_map = {
            "DROPPED": VERDICT_DROPPED,
            "ERROR": VERDICT_ERROR,
            "AUDIT": VERDICT_AUDIT,
        }
        for v in verdict_filter if isinstance(verdict_filter, list) else [verdict_filter]:
            if v.upper() in filter_map:
                verdict_values.append(filter_map[v.upper()])

    while True:
        try:
            channel = grpc_aio.insecure_channel(endpoint)
            stub_module = grpc.protos_and_services("observer/observer.proto")
            stub = stub_module.ObserverStub(channel)

            request_kwargs = {}
            if namespace_filter:
                ns_list = namespace_filter if isinstance(namespace_filter, list) else [namespace_filter]
                request_kwargs["whitelist"] = [
                    {"source_pod": [f"{ns}/"]} for ns in ns_list
                ] + [
                    {"destination_pod": [f"{ns}/"]} for ns in ns_list
                ]

            request = stub_module.GetFlowsRequest(
                follow=True,
                **request_kwargs,
            )

            logger.info("Connecting to Hubble Relay at %s", endpoint)
            async for response in stub.GetFlows(request):
                flow = response.flow
                if flow is None:
                    continue

                flow_dict = json.loads(
                    type(flow).to_json(flow)
                    if hasattr(type(flow), "to_json")
                    else "{}"
                )

                flow_verdict = flow_dict.get("verdict", 0)
                if verdict_values and flow_verdict not in verdict_values:
                    continue

                event = _build_flow_event(flow_dict)
                await queue.put(event)

        except Exception as exc:
            logger.warning(
                "Hubble connection error: %s. Reconnecting in %ds...",
                str(exc),
                reconnect_delay,
            )
            await asyncio.sleep(reconnect_delay)


async def main(queue, args):
    """EDA event source entry point for Cilium policy events.

    Arguments:
        queue: asyncio.Queue for placing events
        args: dict with configuration:
            hubble_endpoint: Hubble Relay gRPC endpoint
            namespace_filter: Namespace to filter on
            verdict_filter: Verdict type to filter (default: DROPPED)
            reconnect_delay: Reconnect delay in seconds
    """
    if not HAS_GRPC:
        logger.error(
            "grpcio is required for cilium_policy_event. "
            "Install with: pip install grpcio"
        )
        return

    endpoint = args.get("hubble_endpoint", "localhost:4245")
    namespace_filter = args.get("namespace_filter", "")
    verdict_filter = args.get("verdict_filter", "DROPPED")
    reconnect_delay = int(args.get("reconnect_delay", 5))

    logger.info(
        "Starting Cilium policy event source: endpoint=%s, "
        "namespace=%s, verdict=%s",
        endpoint,
        namespace_filter,
        verdict_filter,
    )

    await _stream_hubble_flows(
        queue, endpoint, namespace_filter, verdict_filter, reconnect_delay
    )


if __name__ == "__main__":

    class _MockQueue:
        async def put(self, event):
            print(json.dumps(event, indent=2))

    asyncio.run(
        main(
            _MockQueue(),
            {"hubble_endpoint": "localhost:4245", "verdict_filter": "DROPPED"},
        )
    )
