from platformops.integrations.capabilities import (
    K8S_GET_NODES,
    K8S_DIAGNOSE_NAMESPACE,
    K8S_GET_ENDPOINTS,
    K8S_GET_POD,
    K8S_GET_POD_LOGS,
    K8S_INVESTIGATE_NAMESPACE,
    K8S_LIST_INGRESSES,
    K8S_LIST_EVENTS,
    K8S_LIST_NAMESPACES,
    K8S_LIST_PODS,
    K8S_LIST_SERVICES,
)
from platformops.integrations.registry import IntegrationRegistry, PlatformIntegration

__all__ = [
    "IntegrationRegistry",
    "K8S_DIAGNOSE_NAMESPACE",
    "K8S_GET_ENDPOINTS",
    "K8S_GET_NODES",
    "K8S_GET_POD",
    "K8S_GET_POD_LOGS",
    "K8S_INVESTIGATE_NAMESPACE",
    "K8S_LIST_INGRESSES",
    "K8S_LIST_EVENTS",
    "K8S_LIST_NAMESPACES",
    "K8S_LIST_PODS",
    "K8S_LIST_SERVICES",
    "PlatformIntegration",
]
