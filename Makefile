.PHONY: test
test:
	pytest

.PHONY: mcp-fake
mcp-fake:
	PLATFORMOPS_K8S_PROVIDER=fake platformops-mcp-k8s

.PHONY: k8s-nodes
k8s-nodes:
	platformops k8s nodes
