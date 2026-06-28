import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.executors.http_executor import HttpTestExecutor
from app.models.service import (
    DataSource,
    HttpMethod,
    ServiceConfig,
    ServiceType,
    TestCase,
    TestStatus,
    TestSuite,
)


@pytest.fixture
def sample_test_case():
    return TestCase(
        name="Test Happy Path",
        service_name="TestService",
        endpoint_path="/api/test",
        method=HttpMethod.GET,
        full_url="http://localhost:5000/api/test",
        headers={"Content-Type": "application/json"},
        expected_status_code=200,
        data_source=DataSource.ORACLE_DB,
    )


@pytest.fixture
def sample_suite(sample_test_case):
    service = ServiceConfig(
        name="TestService",
        service_type=ServiceType.DOTNET_CORE,
        base_url="http://localhost:5000",
        endpoints=[],
    )
    return TestSuite(
        name="Test Suite",
        service_config=service,
        test_cases=[sample_test_case],
    )


class TestHttpExecutor:
    @pytest.mark.asyncio
    async def test_successful_request(self, sample_suite):
        executor = HttpTestExecutor()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"data": "test"}'
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"data": "test"}

        with patch("httpx.AsyncClient.request", new_callable=AsyncMock, return_value=mock_response):
            report = await executor.execute_suite(sample_suite)

        assert report.total_tests == 1
        assert report.passed == 1
        assert report.failed == 0
        assert report.results[0].status == TestStatus.PASSED

    @pytest.mark.asyncio
    async def test_status_code_mismatch(self, sample_suite):
        executor = HttpTestExecutor()

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = '{"error": "not found"}'
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"error": "not found"}

        with patch("httpx.AsyncClient.request", new_callable=AsyncMock, return_value=mock_response):
            report = await executor.execute_suite(sample_suite)

        assert report.failed == 1
        assert "Expected status 200, got 404" in report.results[0].error_message

    @pytest.mark.asyncio
    async def test_connection_error(self, sample_suite):
        executor = HttpTestExecutor()

        import httpx
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock, side_effect=httpx.ConnectError("Connection refused")):
            report = await executor.execute_suite(sample_suite)

        assert report.errors == 1
        assert report.results[0].status == TestStatus.ERROR
        assert "Connection failed" in report.results[0].error_message

    @pytest.mark.asyncio
    async def test_timeout_error(self, sample_suite):
        executor = HttpTestExecutor()

        import httpx
        with patch("httpx.AsyncClient.request", new_callable=AsyncMock, side_effect=httpx.ReadTimeout("Timed out")):
            report = await executor.execute_suite(sample_suite)

        assert report.errors == 1
        assert "timed out" in report.results[0].error_message.lower()

    @pytest.mark.asyncio
    async def test_content_type_assertion(self):
        tc = TestCase(
            name="Test Content-Type",
            service_name="Svc",
            endpoint_path="/api/x",
            method=HttpMethod.GET,
            full_url="http://localhost:5000/api/x",
            expected_status_code=200,
            expected_response_contains=["application/json"],
            data_source=DataSource.ORACLE_DB,
        )
        service = ServiceConfig(
            name="Svc", service_type=ServiceType.DOTNET_CORE,
            base_url="http://localhost:5000", endpoints=[],
        )
        suite = TestSuite(name="Suite", service_config=service, test_cases=[tc])
        executor = HttpTestExecutor()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "{}"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.json.return_value = {}

        with patch("httpx.AsyncClient.request", new_callable=AsyncMock, return_value=mock_response):
            report = await executor.execute_suite(suite)

        assert report.failed == 1
        assert "content-type" in report.results[0].error_message.lower()

    @pytest.mark.asyncio
    async def test_performance_threshold(self):
        tc = TestCase(
            name="Perf Test",
            service_name="Svc",
            endpoint_path="/api/slow",
            method=HttpMethod.GET,
            full_url="http://localhost:5000/api/slow",
            expected_status_code=200,
            data_source=DataSource.ORACLE_DB,
            tags=["performance"],
        )
        service = ServiceConfig(
            name="Svc", service_type=ServiceType.DOTNET_CORE,
            base_url="http://localhost:5000", endpoints=[],
        )
        suite = TestSuite(name="Suite", service_config=service, test_cases=[tc])
        executor = HttpTestExecutor(max_response_time_ms=1.0)  # 1ms threshold

        import asyncio
        async def slow_request(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "{}"
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {}
            return mock_response

        with patch("httpx.AsyncClient.request", new_callable=AsyncMock, side_effect=slow_request):
            report = await executor.execute_suite(suite)

        assert report.failed == 1
        assert "exceeds threshold" in report.results[0].error_message
