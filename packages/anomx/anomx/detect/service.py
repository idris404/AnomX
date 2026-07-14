"""Anomaly detection orchestration."""

from __future__ import annotations

from typing import Callable
from uuid import UUID

import structlog
from pydantic import BaseModel, Field

from anomx.config.detect_models import DetectConfig
from anomx.config.models import DatabaseSettings
from anomx.core.ensemble import EnsembleDetector
from anomx.detectors.factory import build_detector
from anomx.explain.builder import ExplanationBuilder
from anomx.storage.detection import DetectionRepository
from anomx.storage.postgres import postgres_connection

logger = structlog.get_logger(__name__)


class DetectResult(BaseModel):
    run_id: UUID
    stream_id: UUID
    stream_name: str
    source_run_id: UUID
    observations_scored: int
    alerts_created: int
    ensemble_threshold: float = Field(description="Calibrated percentile threshold on ensemble scores")


class DetectService:
    """Runs detector ensemble on ingested observations and persists alerts."""

    def __init__(
        self,
        database: DatabaseSettings,
        *,
        on_alert_created: Callable[[UUID], None] | None = None,
    ) -> None:
        self._database = database
        self._on_alert_created = on_alert_created

    def detect_stream(self, stream_name: str, config: DetectConfig) -> DetectResult:
        with postgres_connection(self._database.dsn) as connection:
            repository = DetectionRepository(connection)

            stream = repository.get_stream_by_name(stream_name)
            if stream is None:
                msg = f"Stream not found: {stream_name}"
                raise ValueError(msg)

            stream_id = UUID(str(stream["id"]))
            ingestion_run = repository.get_latest_ingestion_run(stream_id)
            if ingestion_run is None:
                msg = f"No completed ingestion run for stream: {stream_name}"
                raise ValueError(msg)

            source_run_id = UUID(str(ingestion_run["id"]))
            records = repository.fetch_observations(stream_id, source_run_id)
            if len(records) < 10:
                msg = f"Not enough observations to detect (need >= 10, got {len(records)})"
                raise ValueError(msg)

            fit_count = max(int(len(records) * config.defaults.fit_ratio), 10)
            fit_count = min(fit_count, len(records) - 1)
            fit_data = records[:fit_count]

            detectors = [build_detector(item.type, item.params) for item in config.detectors]
            names = [item.name for item in config.detectors]
            weights = [item.weight for item in config.detectors]
            ensemble = EnsembleDetector(
                detectors=detectors,
                names=names,
                weights=weights,
                calibration_percentile=config.defaults.calibration.percentile,
            )
            ensemble.fit(fit_data)
            explanation_builder = ExplanationBuilder(
                ensemble=ensemble,
                fit_data=fit_data,
                value_key=config.defaults.value_key,
                ensemble_threshold=ensemble.threshold or 0.0,
            )

            individual = ensemble.individual_scores(records)
            ensemble_scores = ensemble.score(records)
            ensemble_flags = ensemble.predict(records)
            threshold = ensemble.threshold or 0.0

            detection_run_id = repository.create_detection_run(
                stream_id=stream_id,
                source_run_id=source_run_id,
                metadata={"source_run_id": str(source_run_id), "stream_name": stream_name},
            )

            alerts_created = 0
            try:
                detector_flags = {
                    state.name: state.detector.predict(records) for state in ensemble.states
                }

                for index, record in enumerate(records):
                    observation_id = int(record["observation_id"])

                    for detector_name in names:
                        repository.insert_scores(
                            detection_run_id,
                            observation_id,
                            detector_name,
                            float(individual[detector_name][index]),
                            detector_flags[detector_name][index],
                        )

                    ensemble_score = float(ensemble_scores[index])
                    is_ensemble_anomaly = ensemble_flags[index]
                    repository.insert_scores(
                        detection_run_id,
                        observation_id,
                        "ensemble",
                        ensemble_score,
                        is_ensemble_anomaly,
                    )

                    if is_ensemble_anomaly:
                        detector_scores = {
                            name: float(individual[name][index]) for name in names
                        }
                        explanation = explanation_builder.build(
                            record,
                            detector_scores=detector_scores,
                            ensemble_score=ensemble_score,
                        )
                        inserted, alert_id = repository.insert_alert(
                            detection_run_id,
                            stream_id,
                            observation_id,
                            ensemble_score,
                            "ensemble",
                            explanation.to_storage_dict(),
                        )
                        if inserted:
                            alerts_created += 1
                        if self._on_alert_created is not None:
                            self._on_alert_created(alert_id)

                repository.complete_detection_run(
                    detection_run_id,
                    {
                        "source_run_id": str(source_run_id),
                        "observations_scored": len(records),
                        "alerts_created": alerts_created,
                        "ensemble_threshold": threshold,
                    },
                )
            except Exception as exc:
                repository.fail_detection_run(detection_run_id, str(exc))
                logger.exception("detect_failed", stream=stream_name, run_id=str(detection_run_id))
                raise

            logger.info(
                "detect_complete",
                stream=stream_name,
                run_id=str(detection_run_id),
                observations=len(records),
                alerts=alerts_created,
            )
            return DetectResult(
                run_id=detection_run_id,
                stream_id=stream_id,
                stream_name=stream_name,
                source_run_id=source_run_id,
                observations_scored=len(records),
                alerts_created=alerts_created,
                ensemble_threshold=threshold,
            )
