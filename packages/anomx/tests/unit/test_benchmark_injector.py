"""Tests for anomaly injector reproducibility."""

from anomx.benchmark.injector import AnomalyInjector, generate_baseline_series


def test_injector_is_reproducible_with_seed() -> None:
    baseline = generate_baseline_series(500, base_value=20.0, seed=7)
    injector_a = AnomalyInjector(seed=99)
    injector_b = AnomalyInjector(seed=99)

    values_a, indices_a, _ = injector_a.inject(baseline, n_anomalies=25, kinds=["point", "drift"])
    values_b, indices_b, _ = injector_b.inject(baseline, n_anomalies=25, kinds=["point", "drift"])

    assert values_a == values_b
    assert indices_a == indices_b


def test_injector_covers_multiple_anomaly_types() -> None:
    baseline = generate_baseline_series(300, base_value=15.0, seed=1)
    injector = AnomalyInjector(seed=2)
    _, indices, injected = injector.inject(
        baseline,
        n_anomalies=30,
        kinds=["point", "contextual", "drift"],
    )

    assert len(indices) >= 30
    kinds = {item.kind.value for item in injected}
    assert "point" in kinds
    assert "contextual" in kinds
    assert "drift" in kinds
