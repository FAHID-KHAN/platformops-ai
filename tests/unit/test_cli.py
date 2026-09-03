from platformops.cli import main


def test_cli_lists_fake_nodes(capsys):
    exit_code = main(["k8s", "--provider", "fake", "nodes"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "platformops-control-plane" in output


def test_cli_can_emit_json(capsys):
    exit_code = main(["--output", "json", "k8s", "--provider", "fake", "namespaces"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"capability": "kubernetes.list_namespaces"' in output


def test_cli_returns_nonzero_for_policy_violation(capsys):
    exit_code = main(
        [
            "k8s",
            "--provider",
            "fake",
            "--allowed-namespaces",
            "default",
            "pods",
            "--namespace",
            "kube-system",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 1
    assert "policy_violation" in output


def test_cli_investigates_fixture_namespace(capsys):
    exit_code = main(
        [
            "k8s",
            "--provider",
            "fixture",
            "--fixture",
            "tests/scenarios/crashloopbackoff.json",
            "--allowed-namespaces",
            "platformops-demo",
            "investigate",
            "--namespace",
            "platformops-demo",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Detected 1 unhealthy pod" in output
    assert "CrashLoopBackOff" in output or "BackOff" in output


def test_cli_accepts_allowed_namespaces_after_subcommand(capsys):
    exit_code = main(
        [
            "k8s",
            "--provider",
            "fixture",
            "--fixture",
            "tests/scenarios/crashloopbackoff.json",
            "investigate",
            "--namespace",
            "platformops-demo",
            "--allowed-namespaces",
            "platformops-demo",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Detected 1 unhealthy pod" in output


def test_cli_diagnoses_fixture_namespace(capsys):
    exit_code = main(
        [
            "diagnose",
            "k8s",
            "--provider",
            "fixture",
            "--fixture",
            "tests/scenarios/crashloopbackoff.json",
            "--namespace",
            "platformops-demo",
            "--allowed-namespaces",
            "platformops-demo",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Status: critical" in output
    assert "crash looping" in output


def test_cli_lists_prometheus_targets(capsys):
    exit_code = main(
        [
            "prometheus",
            "--prometheus-provider",
            "fixture",
            "--prometheus-fixture",
            "tests/scenarios/prometheus_target_down.json",
            "targets",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "jenkins-0" in output
    assert "down" in output


def test_cli_diagnosis_can_use_prometheus_fixture(capsys):
    exit_code = main(
        [
            "diagnose",
            "k8s",
            "--provider",
            "fixture",
            "--fixture",
            "tests/scenarios/healthy_cluster.json",
            "--namespace",
            "jenkins",
            "--prometheus-provider",
            "fixture",
            "--prometheus-fixture",
            "tests/scenarios/prometheus_target_down.json",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Prometheus target is down" in output


def test_cli_diagnoses_service_markdown(capsys):
    exit_code = main(
        [
            "--output",
            "markdown",
            "diagnose",
            "service",
            "checkout-api",
            "--provider",
            "fixture",
            "--fixture",
            "tests/scenarios/service_no_endpoints.json",
            "--namespace",
            "platformops-demo",
            "--allowed-namespaces",
            "platformops-demo",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# Diagnosis: critical" in output
    assert "has no ready endpoints" in output


def test_cli_scans_cluster_across_allowed_namespaces(capsys):
    exit_code = main(
        [
            "scan",
            "cluster",
            "--provider",
            "fixture",
            "--fixture",
            "tests/scenarios/multi_namespace_triage.json",
            "--allowed-namespaces",
            "platformops-demo,jenkins",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Cluster status: critical" in output
    assert "jenkins - jenkins-0 is crash looping" in output
    assert "platformops-demo" in output


def test_cli_cluster_scan_requires_allowed_namespaces(capsys):
    exit_code = main(
        [
            "scan",
            "cluster",
            "--provider",
            "fixture",
            "--fixture",
            "tests/scenarios/multi_namespace_triage.json",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Cluster status: unknown" in output
    assert "requires --allowed-namespaces" in output


def test_cli_lists_argocd_apps(capsys):
    exit_code = main(
        [
            "delivery",
            "--delivery-provider",
            "fixture",
            "--delivery-fixture",
            "tests/scenarios/delivery_unhealthy.json",
            "argocd",
            "apps",
            "--namespace",
            "jenkins",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "jenkins" in output
    assert "OutOfSync" in output
    assert "Degraded" in output


def test_cli_diagnoses_delivery(capsys):
    exit_code = main(
        [
            "diagnose",
            "delivery",
            "--delivery-provider",
            "fixture",
            "--delivery-fixture",
            "tests/scenarios/delivery_unhealthy.json",
            "--namespace",
            "jenkins",
            "--job",
            "platform/jenkins",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Status: critical" in output
    assert "ArgoCD app jenkins is Degraded" in output
    assert "ended with FAILURE" in output


def test_cli_investigates_app_across_sources(capsys):
    exit_code = main(
        [
            "investigate",
            "app",
            "jenkins",
            "--provider",
            "fixture",
            "--fixture",
            "tests/scenarios/multi_namespace_triage.json",
            "--allowed-namespaces",
            "jenkins",
            "--delivery-provider",
            "fixture",
            "--delivery-fixture",
            "tests/scenarios/delivery_unhealthy.json",
            "--namespace",
            "jenkins",
            "--job",
            "platform/jenkins",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Application status: critical" in output
    assert "Likely explanation" in output
    assert "Delivery evidence is correlated" in output
    assert "ArgoCD app jenkins is Degraded" in output
