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
