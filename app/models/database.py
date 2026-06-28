from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    host: str = Field(description="Oracle DB host")
    port: int = Field(default=1521, description="Oracle DB port")
    service_name: str = Field(description="Oracle service name or SID")
    username: str = ""
    password: str = ""
    connection_string: str | None = Field(
        default=None,
        description="Full connection string (overrides host/port/service_name if provided)",
    )


class QueryTestConfig(BaseModel):
    name: str = Field(description="Test name for this query validation")
    query: str = Field(description="SQL query to execute against Oracle DB")
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_row_count: int | None = None
    expected_columns: list[str] | None = None
    expected_values: list[dict[str, Any]] | None = None
    description: str = ""
