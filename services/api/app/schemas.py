"""Pydantic schemas for API responses."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str = Field(examples=["ok"])
    service: str = Field(examples=["anomx-api"])
    version: str = Field(examples=["0.1.0"])
