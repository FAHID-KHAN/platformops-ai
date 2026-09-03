.PHONY: test
test:
	pytest

.PHONY: mcp-fake
mcp-fake:
	PLATFORMOPS_K8S_PROVIDER=fake platformops-mcp-k8s

