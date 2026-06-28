from __future__ import annotations

from app.generators.base import TestGenerator
from app.models.service import DataSource, EndpointConfig, ServiceConfig, TestCase


class DotNetTestGenerator(TestGenerator):
    """Generates regression test cases for .NET Core microservices."""

    def generate_tests_for_endpoint(
        self, service_config: ServiceConfig, endpoint: EndpointConfig
    ) -> list[TestCase]:
        tests: list[TestCase] = []
        headers = self._build_headers(service_config, endpoint)
        full_url = self._build_url(service_config.base_url, endpoint.path)

        # Test 1: Basic connectivity / happy path
        tests.append(
            TestCase(
                name=f"[{service_config.name}] {endpoint.name} - Happy Path",
                description=f"Verify {endpoint.name} returns expected status code {endpoint.expected_status_code}",
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
                tags=["happy-path", "dotnet", endpoint.data_source.value],
            )
        )

        # Test 2: Response format validation
        tests.append(
            TestCase(
                name=f"[{service_config.name}] {endpoint.name} - Response Format",
                description=f"Verify {endpoint.name} returns valid JSON with expected content-type",
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
                tags=["format-validation", "dotnet"],
            )
        )

        # Test 3: Invalid input (if endpoint has path params)
        if "{" in endpoint.path:
            invalid_url = self._build_url(
                service_config.base_url,
                endpoint.path.split("{")[0] + "invalid-id-000",
            )
            tests.append(
                TestCase(
                    name=f"[{service_config.name}] {endpoint.name} - Invalid ID",
                    description=f"Verify {endpoint.name} returns 404 or 400 for invalid input",
                    service_name=service_config.name,
                    endpoint_path=endpoint.path,
                    method=endpoint.method,
                    full_url=invalid_url,
                    headers=headers,
                    expected_status_code=404,
                    data_source=endpoint.data_source,
                    tags=["negative-test", "dotnet"],
                )
            )

        # Test 4: Unauthorized access (if service has auth)
        if service_config.auth_token:
            no_auth_headers = {k: v for k, v in headers.items() if k != service_config.auth_header}
            tests.append(
                TestCase(
                    name=f"[{service_config.name}] {endpoint.name} - Unauthorized",
                    description=f"Verify {endpoint.name} rejects requests without valid auth token",
                    service_name=service_config.name,
                    endpoint_path=endpoint.path,
                    method=endpoint.method,
                    full_url=full_url,
                    headers=no_auth_headers,
                    query_params=endpoint.query_params,
                    expected_status_code=401,
                    data_source=endpoint.data_source,
                    tags=["security", "dotnet"],
                )
            )

        # Test 5: DB-specific test for Oracle inquiry
        if endpoint.data_source == DataSource.ORACLE_DB:
            tests.append(
                TestCase(
                    name=f"[{service_config.name}] {endpoint.name} - DB Query Response Time",
                    description=f"Verify {endpoint.name} Oracle DB inquiry responds within acceptable time",
                    service_name=service_config.name,
                    endpoint_path=endpoint.path,
                    method=endpoint.method,
                    full_url=full_url,
                    headers=headers,
                    query_params=endpoint.query_params,
                    request_body=endpoint.request_body,
                    expected_status_code=endpoint.expected_status_code,
                    data_source=endpoint.data_source,
                    tags=["performance", "oracle-db", "dotnet"],
                )
            )

        # Test 6: External service call timeout handling
        if endpoint.data_source == DataSource.EXTERNAL_SERVICE:
            tests.append(
                TestCase(
                    name=f"[{service_config.name}] {endpoint.name} - External Call Resilience",
                    description=f"Verify {endpoint.name} handles external service dependency gracefully",
                    service_name=service_config.name,
                    endpoint_path=endpoint.path,
                    method=endpoint.method,
                    full_url=full_url,
                    headers=headers,
                    query_params=endpoint.query_params,
                    request_body=endpoint.request_body,
                    expected_status_code=endpoint.expected_status_code,
                    data_source=endpoint.data_source,
                    tags=["resilience", "external-service", "dotnet"],
                )
            )

        return tests
