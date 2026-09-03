from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Sequence

from platformops.mcp.kubernetes_server import (
    diagnose_namespace_payload,
    get_pod_logs_payload,
    get_pod_payload,
    get_nodes_payload,
    investigate_namespace_payload,
    list_events_payload,
    list_namespaces_payload,
    list_pods_payload,
)
from platformops.mcp.prometheus_server import (
    build_prometheus_integration,
    prometheus_alerts_payload,
    prometheus_query_payload,
    prometheus_targets_payload,
)
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.kubernetes import (
    FakeKubernetesProvider,
    FixtureKubernetesProvider,
    KubernetesApiProvider,
    KubernetesIntegration,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="platformops",
        description="Read-only PlatformOps AI investigation tools.",
    )
    parser.add_argument("--output", choices=("table", "json"), default="table")

    subcommands = parser.add_subparsers(dest="area", required=True)
    diagnose = subcommands.add_parser("diagnose", help="Produce deterministic diagnosis reports")
    diagnose_areas = diagnose.add_subparsers(dest="diagnose_area", required=True)
    diagnose_k8s = diagnose_areas.add_parser("k8s", help="Diagnose Kubernetes namespace health")
    _add_k8s_connection_args(diagnose_k8s)
    diagnose_k8s.add_argument("--namespace", "-n", required=True)
    diagnose_k8s.add_argument("--tail-lines", type=int, default=80)
    _add_prometheus_args(diagnose_k8s)
    _add_policy_args(diagnose_k8s)

    prometheus = subcommands.add_parser("prometheus", help="Read-only Prometheus commands")
    _add_prometheus_args(prometheus)
    prometheus_commands = prometheus.add_subparsers(dest="command", required=True)
    prom_query = prometheus_commands.add_parser("query", help="Run a Prometheus instant query")
    prom_query.add_argument("query")
    prometheus_commands.add_parser("targets", help="List Prometheus scrape targets")
    prometheus_commands.add_parser("alerts", help="List Prometheus alerts")

    k8s = subcommands.add_parser("k8s", help="Read-only Kubernetes investigation commands")
    _add_k8s_connection_args(k8s)
    k8s.add_argument("--allowed-namespaces", default="")

    k8s_commands = k8s.add_subparsers(dest="command", required=True)
    nodes = k8s_commands.add_parser("nodes", help="List Kubernetes nodes")
    _add_policy_args(nodes)
    namespaces = k8s_commands.add_parser("namespaces", help="List Kubernetes namespaces")
    _add_policy_args(namespaces)
    pods = k8s_commands.add_parser("pods", help="List Kubernetes pods")
    pods.add_argument("--namespace", "-n", default=None)
    _add_policy_args(pods)
    pod = k8s_commands.add_parser("pod", help="Show Kubernetes pod details")
    pod.add_argument("name")
    pod.add_argument("--namespace", "-n", required=True)
    _add_policy_args(pod)
    events = k8s_commands.add_parser("events", help="List Kubernetes events")
    events.add_argument("--namespace", "-n", required=True)
    events.add_argument("--pod", default=None)
    _add_policy_args(events)
    logs = k8s_commands.add_parser("logs", help="Show a bounded Kubernetes pod log excerpt")
    logs.add_argument("name")
    logs.add_argument("--namespace", "-n", required=True)
    logs.add_argument("--container", "-c", default=None)
    logs.add_argument("--tail-lines", type=int, default=100)
    _add_policy_args(logs)
    investigate = k8s_commands.add_parser("investigate", help="Investigate a namespace")
    investigate.add_argument("--namespace", "-n", required=True)
    investigate.add_argument("--tail-lines", type=int, default=50)
    _add_policy_args(investigate)

    return parser


def _add_policy_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--allowed-namespaces", default=argparse.SUPPRESS)


def _add_k8s_connection_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", choices=("fake", "fixture", "api"), default="api")
    parser.add_argument("--context", default=None)
    parser.add_argument("--in-cluster", action="store_true")
    parser.add_argument("--fixture", default="tests/scenarios/healthy_cluster.json")


def _add_prometheus_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--prometheus-provider", choices=("fake", "fixture", "api"), default=None)
    parser.add_argument("--prometheus-url", default=None)
    parser.add_argument("--prometheus-fixture", default=None)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    payload = asyncio.run(_run(args))
    _print_payload(payload, args.output)
    return 0 if not payload.get("errors") else 1


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    if args.area == "diagnose":
        if args.diagnose_area != "k8s":
            raise ValueError(f"unsupported diagnosis area: {args.diagnose_area}")
        integration = _build_kubernetes_integration(args)
        prometheus = _build_prometheus_integration(args)
        return {
            "diagnosis": await diagnose_namespace_payload(
                namespace=args.namespace,
                tail_lines=args.tail_lines,
                integration=integration,
                prometheus=prometheus,
            )
        }

    if args.area == "prometheus":
        integration = _build_prometheus_integration(args)
        if integration is None:
            raise SystemExit("Prometheus is not configured. Set --prometheus-url or use --prometheus-provider fake.")
        if args.command == "query":
            return await prometheus_query_payload(args.query, integration)
        if args.command == "targets":
            return await prometheus_targets_payload(integration)
        if args.command == "alerts":
            return await prometheus_alerts_payload(integration)
        raise ValueError(f"unsupported prometheus command: {args.command}")

    if args.area != "k8s":
        raise ValueError(f"unsupported command area: {args.area}")

    integration = _build_kubernetes_integration(args)
    if args.command == "nodes":
        return await get_nodes_payload(integration)
    if args.command == "namespaces":
        return await list_namespaces_payload(integration)
    if args.command == "pods":
        return await list_pods_payload(namespace=args.namespace, integration=integration)
    if args.command == "pod":
        return await get_pod_payload(namespace=args.namespace, name=args.name, integration=integration)
    if args.command == "events":
        return await list_events_payload(
            namespace=args.namespace,
            pod_name=args.pod,
            integration=integration,
        )
    if args.command == "logs":
        return await get_pod_logs_payload(
            namespace=args.namespace,
            name=args.name,
            container=args.container,
            tail_lines=args.tail_lines,
            integration=integration,
        )
    if args.command == "investigate":
        return await investigate_namespace_payload(
            namespace=args.namespace,
            tail_lines=args.tail_lines,
            integration=integration,
        )
    raise ValueError(f"unsupported k8s command: {args.command}")


def _build_kubernetes_integration(args: argparse.Namespace) -> KubernetesIntegration:
    raw_allowed_namespaces = getattr(args, "allowed_namespaces", "")
    allowed_namespaces = {
        item.strip() for item in raw_allowed_namespaces.split(",") if item.strip()
    }
    if args.provider == "fake":
        provider = FakeKubernetesProvider()
    elif args.provider == "fixture":
        provider = FixtureKubernetesProvider(Path(args.fixture))
    else:
        provider = KubernetesApiProvider(context=args.context, in_cluster=args.in_cluster)

    return KubernetesIntegration(
        provider=provider,
        policy=KubernetesReadOnlyPolicy(allowed_namespaces=allowed_namespaces),
    )


def _build_prometheus_integration(args: argparse.Namespace):
    return build_prometheus_integration(
        provider_name=args.prometheus_provider,
        url=args.prometheus_url,
        fixture=args.prometheus_fixture,
    )


def _print_payload(payload: dict[str, Any], output: str) -> None:
    if output == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    errors = payload.get("errors", [])
    if errors:
        for error in errors:
            print(f"error: {error['code']}: {error['message']}")
        return

    payload_body = payload.get("payload", {})
    if "diagnosis" in payload:
        _print_diagnosis(payload["diagnosis"])
        return

    if "diagnosis" in payload_body:
        _print_diagnosis(payload_body["diagnosis"])
        return

    if "query_result" in payload_body:
        result = payload_body["query_result"]
        print(f"Query: {result['query']}")
        print(f"Type: {result['result_type']}")
        for item in result["result"]:
            print(json.dumps(item, sort_keys=True))
        return

    if "targets" in payload_body:
        _print_table(
            ("health", "job", "instance", "scrape_url", "error"),
            [
                (
                    target["health"],
                    target["job"] or "",
                    target["instance"] or "",
                    target["scrape_url"],
                    target["last_error"] or "",
                )
                for target in payload_body["targets"]
            ],
        )
        return

    if "alerts" in payload_body:
        _print_table(
            ("state", "name", "severity", "summary"),
            [
                (
                    alert["state"],
                    alert["name"],
                    alert["severity"] or "",
                    alert["summary"] or "",
                )
                for alert in payload_body["alerts"]
            ],
        )
        return

    if "unhealthy_pods" in payload_body:
        print(payload_body["summary"])
        pods = payload_body["unhealthy_pods"] or payload_body.get("attention_pods", []) or payload_body["pods"]
        if pods:
            print("\npods")
            _print_table(
                ("namespace", "name", "phase", "ready", "restarts", "node"),
                [
                    (
                        pod["namespace"],
                        pod["name"],
                        pod["phase"],
                        pod["ready"],
                        str(pod["restarts"]),
                        pod["node_name"] or "",
                    )
                    for pod in pods
                ],
            )
        if payload_body["events"]:
            print("\nevents")
            _print_table(
                ("type", "reason", "object", "count", "message"),
                [
                    (
                        event["type"],
                        event["reason"],
                        f"{event['involved_object_kind']}/{event['involved_object_name']}",
                        str(event["count"]),
                        event["message"],
                    )
                    for event in payload_body["events"][:10]
                ],
            )
        if payload_body["log_excerpts"]:
            print("\nlog excerpts")
            for logs in payload_body["log_excerpts"]:
                print(f"\n{logs['namespace']}/{logs['pod_name']} tail={logs['tail_lines']}")
                print(logs.get("text", logs.get("error", "")))
        return

    if "nodes" in payload_body:
        _print_table(
            ("name", "ready", "roles", "version"),
            [
                (
                    node["name"],
                    str(node["ready"]),
                    ", ".join(node["roles"]),
                    node["kubernetes_version"] or "",
                )
                for node in payload_body["nodes"]
            ],
        )
        return

    if "namespaces" in payload_body:
        _print_table(
            ("name", "status"),
            [(namespace["name"], namespace["status"]) for namespace in payload_body["namespaces"]],
        )
        return

    if "pods" in payload_body:
        _print_table(
            ("namespace", "name", "phase", "ready", "restarts", "node"),
            [
                (
                    pod["namespace"],
                    pod["name"],
                    pod["phase"],
                    pod["ready"],
                    str(pod["restarts"]),
                    pod["node_name"] or "",
                )
                for pod in payload_body["pods"]
            ],
        )
        return

    if "pod" in payload_body:
        pod = payload_body["pod"]
        print(f"{pod['namespace']}/{pod['name']}")
        print(f"phase: {pod['phase']}")
        print(f"ready: {pod['ready']}")
        print(f"restarts: {pod['restarts']}")
        print(f"node: {pod['node_name'] or ''}")
        print(f"service_account: {pod['service_account'] or ''}")
        if pod["containers"]:
            print("\ncontainers")
            _print_table(
                ("name", "ready", "restarts", "state", "reason"),
                [
                    (
                        container["name"],
                        str(container["ready"]),
                        str(container["restart_count"]),
                        container["state"],
                        container["reason"] or "",
                    )
                    for container in pod["containers"]
                ],
            )
        return

    if "events" in payload_body:
        _print_table(
            ("type", "reason", "object", "count", "message"),
            [
                (
                    event["type"],
                    event["reason"],
                    f"{event['involved_object_kind']}/{event['involved_object_name']}",
                    str(event["count"]),
                    event["message"],
                )
                for event in payload_body["events"]
            ],
        )
        return

    if "logs" in payload_body:
        logs = payload_body["logs"]
        print(f"{logs['namespace']}/{logs['pod_name']} tail={logs['tail_lines']}")
        if logs["container"]:
            print(f"container: {logs['container']}")
        print(logs["text"])
        return

    print("No results.")


def _print_table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    header_line = "  ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    separator = "  ".join("-" * width for width in widths)
    print(header_line)
    print(separator)
    for row in rows:
        print("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))


def _print_diagnosis(report: dict[str, Any]) -> None:
    print(f"Status: {report['status']}")
    print(report["summary"])
    if report["findings"]:
        print("\nFindings")
        for finding in report["findings"]:
            print(f"- [{finding['severity']}] {finding['title']}")
            print(f"  {finding['summary']}")
    if report["recommendations"]:
        print("\nRecommended next actions")
        for recommendation in report["recommendations"]:
            print(f"- {recommendation['action']}")
    if report["limitations"]:
        print("\nLimitations")
        for limitation in report["limitations"]:
            print(f"- {limitation}")


if __name__ == "__main__":
    raise SystemExit(main())
