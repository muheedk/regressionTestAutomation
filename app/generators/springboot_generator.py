from __future__ import annotations

from app.generators.base import TestGenerator
from app.models.service import DataSource, EndpointConfig, HttpMethod, ServiceConfig, TestCase, TestSuite


class SpringBootTestGenerator(TestGenerator):
    """Generates regression test cases for Java Spring Boot microservices."""

    def generate_suite(self, service_config: ServiceConfig) -> TestSuite:
        suite = super().generate_suite(service_config)
        # Add a single actuator health check per service (not per endpoint)
        actuator_url = self._build_url(service_config.base_url, "/actuator/health")
        suite.test_cases.append(
            TestCase(
                name=f"[{service_config.name}] Actuator Health Check",
                description="Verify Spring Boot actuator health endpoint returns UP status",
                service_name=service_config.name,
                endpoint_path="/actuator/health",
                method=HttpMethod.GET,
                full_url=actuator_url,
                headers={"Accept": "application/json"},
                expected_status_code=200,
                expected_response_contains=["UP"],
                data_source=DataSource.ORACLE_DB,
                tags=["health-check", "spring-boot"],
            )
        )
        return suite

    def generate_tests_for_endpoint(
        self, service_config: ServiceConfig, endpoint: EndpointConfig
    ) -> list[TestCase]:
        tests: list[TestCase] = []
        headers = self._build_headers(service_config, endpoint)
        full_url = self._build_url(service_config.base_url, endpoint.path)

        # Test 1: Happy path
        tests.append(
            TestCase(
                name=f"[{service_config.name}] {endpoint.name} - Happy Path",
                description=f"Verify {endpoint.name} returns expected response",
                service_name=service_config.name,
                endpoint_path=endpoint.path,
                method=endpoint.method,
                full_url=full_url,
                headers=headers,
                query_params=endpoint.query_params,
                request_body=endpoint.request_body,
                expected_status_code=endpoint.expected_status_code,
                expected_response_schema=endpoint.expected_response_schema,
                data_source=endpoint.data_source,
                tags=["happy-path", "spring-boot", endpoint.data_source.value],
            )
        )

        # Test 2: Response content-type validation
        tests.append(
            TestCase(
                name=f"[{service_config.name}] {endpoint.name} - Content-Type Validation",
                description=f"Verify {endpoint.name} returns application/json content type",
                service_name=service_config.name,
                endpoint_path=endpoint.path,
                method=endpoint.method,
                full_url=full_url,
                headers=headers,
                query_params=endpoint.query_params,
                request_body=endpoint.request_body,
                expected_status_code=endpoint.expected_status_code,
                expected_response_contains=["application/json"],
                data_source=endpoint.data_source,
                tags=["format-validation", "spring-boot"],
            )
        )

        # Test 3: Invalid path parameter
        if "{" in endpoint.path:
            invalid_url = self._build_url(
                service_config.base_url,
                endpoint.path.split("{")[0] + "invalid-id-999",
            )
            tests.append(
                TestCase(
                    name=f"[{service_config.name}] {endpoint.name} - Not Found",
                    description=f"Verify {endpoint.name} returns 404 for non-existent resource",
                    service_name=service_config.name,
                    endpoint_path=endpoint.path,
                    method=endpoint.method,
                    full_url=invalid_url,
                    headers=headers,
                    expected_status_code=404,
                    data_source=endpoint.data_source,
                    tags=["negative-test", "spring-boot"],
                )
            )

        # Test 5: Auth check
        if service_config.auth_token:
            no_auth_headers = {k: v for k, v in headers.items() if k != service_config.auth_header}
            tests.append(
                TestCase(
                    name=f"[{service_config.name}] {endpoint.name} - Unauthorized",
                    description=f"Verify {endpoint.name} returns 401/403 without auth",
                    service_name=service_config.name,
                    endpoint_path=endpoint.path,
                    method=endpoint.method,
                    full_url=full_url,
                    headers=no_auth_headers,
                    query_params=endpoint.query_params,
                    expected_status_code=401,
                    data_source=endpoint.data_source,
                    tags=["security", "spring-boot"],
                )
            )

        # Test 6: Oracle DB inquiry specific
        if endpoint.data_source == DataSource.ORACLE_DB:
            tests.append(
                TestCase(
                    name=f"[{service_config.name}] {endpoint.name} - DB Query Performance",
                    description=f"Verify {endpoint.name} Oracle DB query completes within SLA",
                    service_name=service_config.name,
                    endpoint_path=endpoint.path,
                    method=endpoint.method,
                    full_url=full_url,
                    headers=headers,
                    query_params=endpoint.query_params,
                    request_body=endpoint.request_body,
                    expected_status_code=endpoint.expected_status_code,
                    data_source=endpoint.data_source,
                    tags=["performance", "oracle-db", "spring-boot"],
                )
            )

        # Test 7: External service dependency
        if endpoint.data_source == DataSource.EXTERNAL_SERVICE:
            tests.append(
                TestCase(
                    name=f"[{service_config.name}] {endpoint.name} - External Service Resilience",
                    description=f"Verify {endpoint.name} handles external service failures gracefully",
                    service_name=service_config.name,
                    endpoint_path=endpoint.path,
                    method=endpoint.method,
                    full_url=full_url,
                    headers=headers,
                    query_params=endpoint.query_params,
                    request_body=endpoint.request_body,
                    expected_status_code=endpoint.expected_status_code,
                    data_source=endpoint.data_source,
                    tags=["resilience", "external-service", "spring-boot"],
                )
            )

        return tests
