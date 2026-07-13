"""Quickstart example — verifies the anomx package is importable."""

from anomx import __version__
from anomx.core.pipeline import Pipeline


class _DemoSource:
    def read(self) -> list[dict[str, float]]:
        return [{"value": 1.0}, {"value": 2.0}, {"value": 99.0}]


class _DemoSink:
    def write(self, records: list[dict[str, float]]) -> int:
        print(f"Received {len(records)} records")  # noqa: T201
        return len(records)


def main() -> None:
    print(f"AnomX v{__version__}")  # noqa: T201
    result = Pipeline(source=_DemoSource(), sink=_DemoSink()).run()
    print(f"Pipeline result: {result}")  # noqa: T201


if __name__ == "__main__":
    main()
