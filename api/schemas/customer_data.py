from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CustomerDataType = Literal["portfolio", "pipeline", "comp_set"]


class StagedRunSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run_id: str = Field(serialization_alias="runId")
    client_id: str = Field(serialization_alias="clientId")
    type: CustomerDataType
    row_count: int = Field(serialization_alias="rowCount")
    error_count: int = Field(serialization_alias="errorCount")
    created_at: str = Field(serialization_alias="createdAt")


class ImportResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    run: StagedRunSummary
    errors_preview: list[dict] = Field(default_factory=list, serialization_alias="errorsPreview")
