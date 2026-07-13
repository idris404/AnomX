"""Tests for core protocol interfaces."""

from typing import Any

from anomx.core.interfaces import Alerter, Detector, Sink, Source


class _FakeSource:
    def read(self) -> list[dict[str, Any]]:
        return [{"value": 1.0}]


class _FakeSink:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def write(self, records: list[dict[str, Any]]) -> int:
        self.records.extend(records)
        return len(records)


class _FakeDetector:
    def fit(self, data: list[dict[str, Any]]) -> None:
        pass

    def score(self, data: list[dict[str, Any]]) -> list[float]:
        return [0.1] * len(data)

    def predict(self, data: list[dict[str, Any]]) -> list[bool]:
        return [False] * len(data)


class _FakeAlerter:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    def send(self, alert: dict[str, Any]) -> None:
        self.sent.append(alert)


def test_source_protocol() -> None:
    assert isinstance(_FakeSource(), Source)


def test_sink_protocol() -> None:
    assert isinstance(_FakeSink(), Sink)


def test_detector_protocol() -> None:
    assert isinstance(_FakeDetector(), Detector)


def test_alerter_protocol() -> None:
    assert isinstance(_FakeAlerter(), Alerter)
