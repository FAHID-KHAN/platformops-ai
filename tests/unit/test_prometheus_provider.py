from pathlib import Path

from platformops.providers.prometheus import FixturePrometheusProvider


async def test_fixture_prometheus_provider_returns_targets_and_alerts():
    provider = FixturePrometheusProvider(Path("tests/scenarios/prometheus_target_down.json"))

    targets = await provider.targets()
    alerts = await provider.alerts()
    result = await provider.query("up")

    assert targets[0].health == "down"
    assert alerts[0].state == "firing"
    assert result.query == "up"

