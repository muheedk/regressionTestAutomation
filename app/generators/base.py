from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.service import EndpointConfig, ServiceConfig, TestCase, TestSuite


class TestGenerator(ABC):
    """Base class for test case generators."""

    def generate_suite(self, service_config: ServiceConfig) -> TestSuite:
        test_cases = []
        for endpoint in service_config.endpoints:
            test_cases.extend(self.generate_tests_for_endpoint(service_config, endpoint))

        return TestSuite(
            name=f"Regression Tests - {service_config.name}",
            description=f"Auto-generated regression test suite for {service_config.name} ({service_config.service_type.value})",
            service_config=service_config,
            test_cases=test_cases,
        )

    @abstractmethod
    def generate_tests_for_endpoint(
        self, service_config: ServiceConfig, endpoint: EndpointConfig
    ) -> list[TestCase]:
        pass

    def _build_url(self, base_url: str, path: str) -> str:
        base = base_url.rstrip("/")
        path = path if path.startswith("/") else f"/{path}"
        return f"{base}{path}"

    def _build_headers(self, service_config: ServiceConfig, endpoint: EndpointConfig) -> dict[str, str]:
        headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        if service_config.auth_header and service_config.auth_token:
            headers[service_config.auth_header] = service_config.auth_token
        for h in endpoint.headers:
            headers[h.key] = h.value
        return headers
