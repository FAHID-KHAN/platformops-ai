from __future__ import annotations


class PolicyViolation(ValueError):
    """Raised when a requested operation exceeds configured read-only policy."""


class KubernetesReadOnlyPolicy:
    def __init__(self, allowed_namespaces: set[str] | None = None) -> None:
        self.allowed_namespaces = allowed_namespaces or set()

    def ensure_namespace_allowed(self, namespace: str | None) -> None:
        if namespace is None or not self.allowed_namespaces:
            return
        if namespace not in self.allowed_namespaces:
            allowed = ", ".join(sorted(self.allowed_namespaces))
            raise PolicyViolation(
                f"namespace '{namespace}' is not allowed by policy; allowed namespaces: {allowed}"
            )

    def filter_namespaces(self, namespaces: list[str]) -> list[str]:
        if not self.allowed_namespaces:
            return namespaces
        return [namespace for namespace in namespaces if namespace in self.allowed_namespaces]

