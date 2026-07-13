"""Tests for the minimal pipeline."""

from typing import Any

from anomx.core.pipeline import Pipeline


class _ListSource:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = records

    def read(self) -> list[dict[str, Any]]:
        return self._records


class _CollectSink:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def write(self, records: list[dict[str, Any]]) -> int:
        self.records.extend(records)
        return len(records)


def test_pipeline_run() -> None:
    source = _ListSource([{"value": 42.0}, {"value": 43.0}])
    sink = _CollectSink()
    pipeline = Pipeline(source=source, sink=sink)

    result = pipeline.run()

    assert result == {"records_read": 2, "records_written": 2}
    assert len(sink.records) == 2
