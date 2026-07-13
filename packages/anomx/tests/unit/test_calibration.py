"""Tests for calibration utilities."""

import pytest

from anomx.core.calibration import percentile_threshold


def test_percentile_threshold() -> None:
    scores = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    threshold = percentile_threshold(scores, percentile=90.0)
    assert threshold == 9.0


def test_percentile_threshold_empty_raises() -> None:
    with pytest.raises(ValueError, match="scores must not be empty"):
        percentile_threshold([])
