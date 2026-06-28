from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ServiceType(str, Enum):
    DOTNET_CORE = "dotnet_core"
    JAVA_SPRING_BOOT = "java_spring_boot"


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class DataSource(str, Enum):
    ORACLE_DB = "oracle_db"
    EXTERNAL_SERVICE = "external_service"


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class HeaderConfig(BaseModel):
    key: str
    value: str


class EndpointConfig(BaseModel):
    name: str = Field(description="Friendly name for the endpoint")
    path: str = Field(description="Endpoint path (e.g., /api/customers/{id})")
    method: HttpMethod = HttpMethod.GET
    headers: list[HeaderConfig] = Field(default_factory=list)
    query_params: dict[str, str] = Field(default_factory=dict)
    request_body: dict[str, Any] | None = None
    data_source: DataSource = DataSource.ORACLE_DB
    expected_status_code: int = 200
    expected_response_schema: dict[str, Any] | None = None
    description: str = ""


class ServiceConfig(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(description="Service name (e.g., CustomerService)", max_length=200)
    service_type: ServiceType
    base_url: str = Field(description="Base URL of the service (e.g., http://localhost:5001)", max_length=2000)
    endpoints: list[EndpointConfig] = Field(default_factory=list, max_length=100)
    auth_header: str | None = None
    auth_token: str | None = None
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("base_url")
    @classmethod
    def validate_url_scheme(cls, v: str) -> str:
        allowed_schemes = ("http://", "https://")
        if not v.lower().startswith(allowed_schemes):
            raise ValueError("base_url must start with http:// or https://")
        return v


class TestCase(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    service_name: str
    endpoint_path: str
    method: HttpMethod
    full_url: str
    headers: dict[str, str] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    request_body: dict[str, Any] | None = None
    expected_status_code: int = 200
    expected_response_contains: list[str] = Field(default_factory=list)
    expected_response_schema: dict[str, Any] | None = None
    data_source: DataSource = DataSource.ORACLE_DB
    tags: list[str] = Field(default_factory=list)


class TestSuite(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    service_config: ServiceConfig
    test_cases: list[TestCase] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TestResult(BaseModel):
    test_case_id: UUID
    test_name: str
    status: TestStatus
    response_status_code: int | None = None
    response_body: Any = None
    response_time_ms: float = 0.0
    error_message: str | None = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    executed_at: datetime = Field(default_factory=datetime.utcnow)


class ExecutionReport(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    suite_name: str
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    total_duration_ms: float = 0.0
    results: list[TestResult] = Field(default_factory=list)
    executed_at: datetime = Field(default_factory=datetime.utcnow)
