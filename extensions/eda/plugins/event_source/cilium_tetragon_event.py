"""
cilium_tetragon_event - Stream Tetragon security events.

Connects to the Tetragon gRPC endpoint and streams runtime security events
including process execution, process exit, and kernel probe events.

Arguments:
    tetragon_endpoint: Tetragon gRPC endpoint (default: 127.0.0.1:54321)
    event_types: List of event types to stream (default: [process_exec, process_exit, process_kprobe])
    namespace_filter: Filter events by namespace (default: empty, all namespaces)
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


EVENT_TYPE_MAP = {
    "process_exec": 1,
    "process_exit": 5,
    "process_kprobe": 9,
    "process_tracepoint": 10,
    "process_loader": 11,
    "process_uprobe": 12,
}


def _extract_process_info(process_data):
    """Extract key fields from a Tetragon process object."""
    if not process_data:
        return {}
    return {
        "pid": process_data.get("pid", 0),
        "uid": process_data.get("uid", 0),
        "binary": process_data.get("binary", ""),
        "arguments": process_data.get("arguments", ""),
        "flags": process_data.get("flags", ""),
        "start_time": process_data.get("start_time", ""),
        "pod": {
            "namespace": process_data.get("pod", {}).get("namespace", ""),
            "name": process_data.get("pod", {}).get("name", ""),
            "container": {
                "name": process_data.get("pod", {}).get("container", {}).get("name", ""),
                "image": process_data.get("pod", {}).get("container", {}).get("image", {}).get("image", ""),
            },
        },
        "cap": {
            "permitted": process_data.get("cap", {}).get("permitted", []),
            "effective": process_data.get("cap", {}).get("effective", []),
        },
        "ns": process_data.get("ns", {}),
    }


def _build_tetragon_event(event_data, event_type):
    """Convert a Tetragon event into a normalized EDA event."""
    base_event = {
        "event_type": f"tetragon_{event_type}",
        "timestamp": event_data.get("time", datetime.now(timezone.utc).isoformat()),
        "node_name": event_data.get("node_name", ""),
    }

    if event_type == "process_exec":
        exec_data = event_data.get("process_exec", {})
        base_event["process"] = _extract_process_info(exec_data.get("process", {}))
        base_event["parent"] = _extract_process_info(exec_data.get("parent", {}))
        base_event["ancestors"] = [
            _extract_process_info(a) for a in exec_data.get("ancestors", [])
        ]

    elif event_type == "process_exit":
        exit_data = event_data.get("process_exit", {})
        base_event["process"] = _extract_process_info(exit_data.get("process", {}))
        base_event["parent"] = _extract_process_info(exit_data.get("parent", {}))
        base_event["signal"] = exit_data.get("signal", "")
        base_event["status"] = exit_data.get("status", 0)

    elif event_type == "process_kprobe":
        kprobe_data = event_data.get("process_kprobe", {})
        base_event["process"] = _extract_process_info(kprobe_data.get("process", {}))
        base_event["parent"] = _extract_process_info(kprobe_data.get("parent", {}))
        base_event["function_name"] = kprobe_data.get("function_name", "")
        base_event["args"] = kprobe_data.get("args", [])
        base_event["return"] = kprobe_data.get("return", {})
        base_event["action"] = kprobe_data.get("action", "")
        base_event["policy_name"] = kprobe_data.get("policy_name", "")

    return base_event


def _matches_namespace(event_data, namespace_filter):
    """Check if event belongs to the filtered namespace."""
    if not namespace_filter:
        return True

    ns_list = namespace_filter if isinstance(namespace_filter, list) else [namespace_filter]

    for etype in ["process_exec", "process_exit", "process_kprobe"]:
        edata = event_data.get(etype, {})
        if edata:
            proc = edata.get("process", {})
            pod_ns = proc.get("pod", {}).get("namespace", "")
            if pod_ns in ns_list:
                return True
    return False


async def _stream_tetragon_events(queue, endpoint, event_types, namespace_filter, reconnect_delay):
    """Stream events from Tetragon using gRPC."""
    type_nums = [EVENT_TYPE_MAP.get(et, 0) for et in event_types if et in EVENT_TYPE_MAP]

    while True:
        try:
            channel = grpc_aio.insecure_channel(endpoint)
            stub_module = grpc.protos_and_services("tetragon/events.proto")
            stub = stub_module.FineGuidanceSensorsStub(channel)

            request_kwargs = {}
            if type_nums:
                request_kwargs["allow_list"] = [
                    {"event_set": type_nums}
                ]

            request = stub_module.GetEventsRequest(
                **request_kwargs,
            )

            logger.info("Connecting to Tetragon at %s", endpoint)
            async for response in stub.GetEvents(request):
                event_dict = json.loads(
                    type(response).to_json(response)
                    if hasattr(type(response), "to_json")
                    else "{}"
                )

                if not _matches_namespace(event_dict, namespace_filter):
                    continue

                for etype in event_types:
                    if etype in event_dict or f"process_{etype}" in event_dict:
                        event = _build_tetragon_event(event_dict, etype)
                        await queue.put(event)
                        break
                else:
                    for etype in event_types:
                        if event_dict.get(etype):
                            event = _build_tetragon_event(event_dict, etype)
                            await queue.put(event)
                            break

        except Exception as exc:
            logger.warning(
                "Tetragon connection error: %s. Reconnecting in %ds...",
                str(exc),
                reconnect_delay,
            )
            await asyncio.sleep(reconnect_delay)


async def main(queue, args):
    """EDA event source entry point for Tetragon security events.

    Arguments:
        queue: asyncio.Queue for placing events
        args: dict with configuration:
            tetragon_endpoint: Tetragon gRPC endpoint
            event_types: List of event types to stream
            namespace_filter: Namespace filter
            reconnect_delay: Reconnect delay in seconds
    """
    if not HAS_GRPC:
        logger.error(
            "grpcio is required for cilium_tetragon_event. "
            "Install with: pip install grpcio"
        )
        return

    endpoint = args.get("tetragon_endpoint", "127.0.0.1:54321")
    event_types = args.get(
        "event_types", ["process_exec", "process_exit", "process_kprobe"]
    )
    namespace_filter = args.get("namespace_filter", "")
    reconnect_delay = int(args.get("reconnect_delay", 5))

    logger.info(
        "Starting Tetragon event source: endpoint=%s, types=%s, namespace=%s",
        endpoint,
        event_types,
        namespace_filter,
    )

    await _stream_tetragon_events(
        queue, endpoint, event_types, namespace_filter, reconnect_delay
    )


if __name__ == "__main__":

    class _MockQueue:
        async def put(self, event):
            print(json.dumps(event, indent=2))

    asyncio.run(
        main(
            _MockQueue(),
            {
                "tetragon_endpoint": "127.0.0.1:54321",
                "event_types": ["process_exec", "process_kprobe"],
            },
        )
    )
