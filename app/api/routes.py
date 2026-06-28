from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.core.test_store import TestStore
from app.executors.http_executor import HttpTestExecutor
from app.generators.dotnet_generator import DotNetTestGenerator
from app.generators.springboot_generator import SpringBootTestGenerator
from app.models.service import (
    ExecutionReport,
    ServiceConfig,
    ServiceType,
    TestSuite,
)

router = APIRouter(prefix="/api")
store = TestStore()
executor = HttpTestExecutor()


@router.post("/services", response_model=ServiceConfig)
async def create_service(config: ServiceConfig) -> ServiceConfig:
    return store.add_service(config)


@router.get("/services", response_model=list[ServiceConfig])
async def list_services() -> list[ServiceConfig]:
    return store.get_all_services()


@router.get("/services/{service_id}", response_model=ServiceConfig)
async def get_service(service_id: UUID) -> ServiceConfig:
    service = store.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.delete("/services/{service_id}")
async def delete_service(service_id: UUID) -> dict:
    if not store.delete_service(service_id):
        raise HTTPException(status_code=404, detail="Service not found")
    return {"message": "Service deleted"}


@router.post("/generate/{service_id}", response_model=TestSuite)
async def generate_tests(service_id: UUID) -> TestSuite:
    service = store.get_service(service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service.service_type == ServiceType.DOTNET_CORE:
        generator = DotNetTestGenerator()
    else:
        generator = SpringBootTestGenerator()

    suite = generator.generate_suite(service)
    store.add_suite(suite)
    return suite


@router.get("/suites", response_model=list[TestSuite])
async def list_suites() -> list[TestSuite]:
    return store.get_all_suites()


@router.get("/suites/{suite_id}", response_model=TestSuite)
async def get_suite(suite_id: UUID) -> TestSuite:
    suite = store.get_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return suite


@router.delete("/suites/{suite_id}")
async def delete_suite(suite_id: UUID) -> dict:
    if not store.delete_suite(suite_id):
        raise HTTPException(status_code=404, detail="Test suite not found")
    return {"message": "Test suite deleted"}


@router.post("/execute/{suite_id}", response_model=ExecutionReport)
async def execute_tests(suite_id: UUID) -> ExecutionReport:
    suite = store.get_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")

    report = await executor.execute_suite(suite)
    store.add_report(report)
    return report


@router.get("/reports", response_model=list[ExecutionReport])
async def list_reports() -> list[ExecutionReport]:
    return store.get_all_reports()


@router.get("/reports/{report_id}", response_model=ExecutionReport)
async def get_report(report_id: UUID) -> ExecutionReport:
    report = store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report
