"""Anomaly injection for controlled benchmark evaluation."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class AnomalyKind(str, Enum):
    POINT = "point"
    CONTEXTUAL = "contextual"
    DRIFT = "drift"


@dataclass(frozen=True)
class InjectedAnomaly:
    index: int
    kind: AnomalyKind


class AnomalyInjector:
    """Inject point, contextual, and drift anomalies into a baseline series."""

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)

    def inject(
        self,
        values: list[float],
        n_anomalies: int,
        kinds: list[Literal["point", "contextual", "drift"]] | None = None,
    ) -> tuple[list[float], set[int], list[InjectedAnomaly]]:
        if n_anomalies <= 0:
            return list(values), set(), []

        allowed = [AnomalyKind(kind) for kind in (kinds or ["point", "contextual", "drift"])]
        indices = self._select_indices(len(values), n_anomalies)
        injected: list[InjectedAnomaly] = []
        mutated = list(values)
        anomaly_indices: set[int] = set()

        for index in indices:
            kind = self._rng.choice(allowed)
            if kind == AnomalyKind.POINT:
                mutated[index] = self._inject_point(mutated[index])
            elif kind == AnomalyKind.CONTEXTUAL:
                mutated[index] = self._inject_contextual(mutated, index)
            else:
                self._inject_drift(mutated, index)
                anomaly_indices.update(range(index, min(index + 5, len(mutated))))

            injected.append(InjectedAnomaly(index=index, kind=kind))
            anomaly_indices.add(index)

        return mutated, anomaly_indices, injected

    def _select_indices(self, length: int, n_anomalies: int) -> list[int]:
        if n_anomalies >= length:
            msg = "n_anomalies must be smaller than series length"
            raise ValueError(msg)
        start = max(10, int(length * 0.1))
        end = max(start + 1, int(length * 0.9))
        pool = list(range(start, end))
        return sorted(self._rng.sample(pool, n_anomalies))

    def _inject_point(self, value: float) -> float:
        return value + self._rng.choice([-1, 1]) * self._rng.uniform(20, 40)

    def _inject_contextual(self, values: list[float], index: int) -> float:
        window = values[max(0, index - 5) : index]
        local_mean = sum(window) / len(window) if window else values[index]
        # Contextual: spike relative to local context, not global baseline
        return local_mean + self._rng.uniform(8, 15)

    def _inject_drift(self, values: list[float], index: int) -> None:
        shift = self._rng.uniform(5, 10)
        for offset in range(5):
            pos = index + offset
            if pos >= len(values):
                break
            values[pos] += shift * math.exp(-0.3 * offset)


def generate_baseline_series(
    n_samples: int,
    base_value: float,
    seed: int,
) -> list[float]:
    rng = random.Random(seed)
    return [base_value + math.sin(index / 25.0) + rng.gauss(0, 0.5) for index in range(n_samples)]
