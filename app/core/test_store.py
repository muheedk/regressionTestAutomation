from __future__ import annotations

from uuid import UUID

from app.models.service import ExecutionReport, ServiceConfig, TestSuite


class TestStore:
    """In-memory store for service configs, test suites, and execution reports."""

    def __init__(self) -> None:
        self._services: dict[UUID, ServiceConfig] = {}
        self._suites: dict[UUID, TestSuite] = {}
        self._reports: dict[UUID, ExecutionReport] = {}

    # Services
    def add_service(self, service: ServiceConfig) -> ServiceConfig:
        self._services[service.id] = service
        return service

    def get_service(self, service_id: UUID) -> ServiceConfig | None:
        return self._services.get(service_id)

    def get_all_services(self) -> list[ServiceConfig]:
        return list(self._services.values())

    def delete_service(self, service_id: UUID) -> bool:
        return self._services.pop(service_id, None) is not None

    # Test Suites
    def add_suite(self, suite: TestSuite) -> TestSuite:
        self._suites[suite.id] = suite
        return suite

    def get_suite(self, suite_id: UUID) -> TestSuite | None:
        return self._suites.get(suite_id)

    def get_all_suites(self) -> list[TestSuite]:
        return list(self._suites.values())

    def delete_suite(self, suite_id: UUID) -> bool:
        return self._suites.pop(suite_id, None) is not None

    # Reports
    def add_report(self, report: ExecutionReport) -> ExecutionReport:
        self._reports[report.id] = report
        return report

    def get_report(self, report_id: UUID) -> ExecutionReport | None:
        return self._reports.get(report_id)

    def get_all_reports(self) -> list[ExecutionReport]:
        return sorted(self._reports.values(), key=lambda r: r.executed_at, reverse=True)
