from __future__ import annotations

import time
from typing import Any

import httpx

from app.models.service import ExecutionReport, TestCase, TestResult, TestStatus, TestSuite


class HttpTestExecutor:
    """Executes test cases by making HTTP requests to service endpoints."""

    def __init__(self, timeout: float = 30.0, max_response_time_ms: float = 5000.0):
        self._timeout = timeout
        self._max_response_time_ms = max_response_time_ms

    async def execute_suite(self, suite: TestSuite) -> ExecutionReport:
        results: list[TestResult] = []

        async with httpx.AsyncClient(timeout=self._timeout, verify=False) as client:
            for test_case in suite.test_cases:
                result = await self._execute_test(client, test_case)
                results.append(result)

        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        total_duration = sum(r.response_time_ms for r in results)

        return ExecutionReport(
            suite_name=suite.name,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            errors=errors,
            skipped=skipped,
            total_duration_ms=total_duration,
            results=results,
        )

    async def _execute_test(self, client: httpx.AsyncClient, test_case: TestCase) -> TestResult:
        start_time = time.perf_counter()
        try:
            response = await client.request(
                method=test_case.method.value,
                url=test_case.full_url,
                headers=test_case.headers,
                params=test_case.query_params if test_case.query_params else None,
                json=test_case.request_body,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            assertions_passed = 0
            assertions_failed = 0
            error_messages: list[str] = []

            # Assert status code
            if response.status_code == test_case.expected_status_code:
                assertions_passed += 1
            else:
                assertions_failed += 1
                error_messages.append(
                    f"Expected status {test_case.expected_status_code}, got {response.status_code}"
                )

            # Assert response contains expected strings
            response_text = response.text
            for expected in test_case.expected_response_contains:
                content_type = response.headers.get("content-type", "")
                if expected == "application/json":
                    if "application/json" in content_type:
                        assertions_passed += 1
                    else:
                        assertions_failed += 1
                        error_messages.append(f"Expected content-type containing '{expected}', got '{content_type}'")
                elif expected in response_text:
                    assertions_passed += 1
                else:
                    assertions_failed += 1
                    error_messages.append(f"Response body does not contain '{expected}'")

            # Assert response schema (basic field presence check)
            if test_case.expected_response_schema and response.status_code == test_case.expected_status_code:
                try:
                    body = response.json()
                    schema_fields = test_case.expected_response_schema.get("properties", {})
                    for field_name in schema_fields:
                        if isinstance(body, dict) and field_name in body:
                            assertions_passed += 1
                        elif isinstance(body, list) and body and field_name in body[0]:
                            assertions_passed += 1
                        else:
                            assertions_failed += 1
                            error_messages.append(f"Response missing expected field '{field_name}'")
                except Exception:
                    pass

            # Performance check for tagged tests
            if "performance" in test_case.tags and elapsed_ms > self._max_response_time_ms:
                assertions_failed += 1
                error_messages.append(
                    f"Response time {elapsed_ms:.0f}ms exceeds threshold {self._max_response_time_ms:.0f}ms"
                )
            elif "performance" in test_case.tags:
                assertions_passed += 1

            status = TestStatus.PASSED if assertions_failed == 0 else TestStatus.FAILED
            response_body = self._safe_json(response)

            return TestResult(
                test_case_id=test_case.id,
                test_name=test_case.name,
                status=status,
                response_status_code=response.status_code,
                response_body=response_body,
                response_time_ms=elapsed_ms,
                error_message="; ".join(error_messages) if error_messages else None,
                assertions_passed=assertions_passed,
                assertions_failed=assertions_failed,
            )

        except httpx.ConnectError as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return TestResult(
                test_case_id=test_case.id,
                test_name=test_case.name,
                status=TestStatus.ERROR,
                response_time_ms=elapsed_ms,
                error_message=f"Connection failed: {e}",
            )
        except httpx.TimeoutException as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return TestResult(
                test_case_id=test_case.id,
                test_name=test_case.name,
                status=TestStatus.ERROR,
                response_time_ms=elapsed_ms,
                error_message=f"Request timed out: {e}",
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return TestResult(
                test_case_id=test_case.id,
                test_name=test_case.name,
                status=TestStatus.ERROR,
                response_time_ms=elapsed_ms,
                error_message=f"Unexpected error: {e}",
            )

    def _safe_json(self, response: httpx.Response) -> Any:
        try:
            return response.json()
        except Exception:
            text = response.text
            return text[:500] if len(text) > 500 else text
