"""
cilium_hubble_flow - Stream all Hubble flow events with configurable filters.

General purpose Hubble flow streaming event source for EDA. Connects to the
Hubble Relay gRPC endpoint and streams flow events matching the configured
source, destination, verdict, and protocol filters.

Arguments:
    hubble_endpoint: Hubble Relay gRPC endpoint (default: localhost:4245)
    source_filter: Filter by source namespace/pod (default: empty)
    destination_filter: Filter by destination namespace/pod (default: empty)
    verdict_filter: Filter by verdict (FORWARDED, DROPPED, etc.)
    protocol_filter: Filter by L4 protocol (TCP, UDP, ICMP)
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

VERDICT_MAP = {
    0: "VERDICT_UNKNOWN",
    1: "FORWARDED",
    2: "DROPPED",
    3: "ERROR",
    4: "REDIRECTED",
    5: "AUDIT",
}

VERDICT_NAME_TO_NUM = {v: k for k, v in VERDICT_MAP.items()}

PROTOCOL_MAP = {
    "TCP": 6,
    "UDP": 17,
    "ICMP": 1,
    "ICMPv6": 58,
}


def _build_flow_event(flow_data):
    """Convert a Hubble flow dict into a normalized EDA event."""
    source = flow_data.get("source", {})
    destination = flow_data.get("destination", {})
    verdict_num = flow_data.get("verdict", 0)

    return {
        "event_type": "cilium_hubble_flow",
        "timestamp": flow_data.get("time", datetime.now(timezone.utc).isoformat()),
        "verdict": VERDICT_MAP.get(verdict_num, "UNKNOWN"),
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
        "node_name": flow_data.get("node_name", ""),
        "is_reply": flow_data.get("is_reply", False),
        "drop_reason": flow_data.get("drop_reason", 0),
        "drop_reason_desc": flow_data.get("drop_reason_desc", ""),
        "summary": flow_data.get("Summary", ""),
    }


def _match_filter(flow_dict, source_filter, destination_filter, verdict_filter, protocol_filter):
    """Check if a flow matches all configured filters."""
    if source_filter:
        src = flow_dict.get("source", {})
        src_id = f"{src.get('namespace', '')}/{src.get('pod_name', '')}"
        if source_filter not in src_id:
            return False

    if destination_filter:
        dst = flow_dict.get("destination", {})
        dst_id = f"{dst.get('namespace', '')}/{dst.get('pod_name', '')}"
        if destination_filter not in dst_id:
            return False

    if verdict_filter:
        flow_verdict = flow_dict.get("verdict", 0)
        expected = VERDICT_NAME_TO_NUM.get(verdict_filter.upper(), -1)
        if expected >= 0 and flow_verdict != expected:
            return False

    if protocol_filter:
        l4 = flow_dict.get("l4", {})
        proto_upper = protocol_filter.upper()
        if proto_upper == "TCP" and "TCP" not in l4:
            return False
        if proto_upper == "UDP" and "UDP" not in l4:
            return False
        if proto_upper == "ICMP" and "ICMPv4" not in l4 and "ICMPv6" not in l4:
            return False

    return True


async def _stream_hubble_flows(
    queue, endpoint, source_filter, destination_filter,
    verdict_filter, protocol_filter, reconnect_delay,
):
    """Stream flows from Hubble Relay using gRPC."""
    while True:
        try:
            channel = grpc_aio.insecure_channel(endpoint)
            stub_module = grpc.protos_and_services("observer/observer.proto")
            stub = stub_module.ObserverStub(channel)

            request = stub_module.GetFlowsRequest(follow=True)

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

                if not _match_filter(
                    flow_dict, source_filter, destination_filter,
                    verdict_filter, protocol_filter
                ):
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
    """EDA event source entry point for Hubble flow streaming.

    Arguments:
        queue: asyncio.Queue for placing events
        args: dict with configuration:
            hubble_endpoint: Hubble Relay gRPC endpoint
            source_filter: Source namespace/pod filter
            destination_filter: Destination namespace/pod filter
            verdict_filter: Verdict filter string
            protocol_filter: Protocol filter (TCP, UDP, ICMP)
            reconnect_delay: Reconnect delay in seconds
    """
    if not HAS_GRPC:
        logger.error(
            "grpcio is required for cilium_hubble_flow. "
            "Install with: pip install grpcio"
        )
        return

    endpoint = args.get("hubble_endpoint", "localhost:4245")
    source_filter = args.get("source_filter", "")
    destination_filter = args.get("destination_filter", "")
    verdict_filter = args.get("verdict_filter", "")
    protocol_filter = args.get("protocol_filter", "")
    reconnect_delay = int(args.get("reconnect_delay", 5))

    logger.info(
        "Starting Hubble flow event source: endpoint=%s, "
        "source=%s, dest=%s, verdict=%s, protocol=%s",
        endpoint,
        source_filter,
        destination_filter,
        verdict_filter,
        protocol_filter,
    )

    await _stream_hubble_flows(
        queue, endpoint, source_filter, destination_filter,
        verdict_filter, protocol_filter, reconnect_delay
    )


if __name__ == "__main__":

    class _MockQueue:
        async def put(self, event):
            print(json.dumps(event, indent=2))

    asyncio.run(
        main(
            _MockQueue(),
            {"hubble_endpoint": "localhost:4245"},
        )
    )
