import pytest

from app.generators.dotnet_generator import DotNetTestGenerator
from app.generators.springboot_generator import SpringBootTestGenerator
from app.models.service import (
    DataSource,
    EndpointConfig,
    HttpMethod,
    ServiceConfig,
    ServiceType,
)


@pytest.fixture
def dotnet_service():
    return ServiceConfig(
        name="CustomerService",
        service_type=ServiceType.DOTNET_CORE,
        base_url="http://localhost:5001",
        endpoints=[
            EndpointConfig(
                name="Get Customer",
                path="/api/customers/{id}",
                method=HttpMethod.GET,
                data_source=DataSource.ORACLE_DB,
                expected_status_code=200,
            ),
            EndpointConfig(
                name="List Accounts",
                path="/api/accounts",
                method=HttpMethod.GET,
                data_source=DataSource.EXTERNAL_SERVICE,
                expected_status_code=200,
            ),
        ],
        auth_header="Authorization",
        auth_token="Bearer test-token",
    )


@pytest.fixture
def spring_service():
    return ServiceConfig(
        name="PaymentService",
        service_type=ServiceType.JAVA_SPRING_BOOT,
        base_url="http://localhost:8080",
        endpoints=[
            EndpointConfig(
                name="Get Payment",
                path="/api/payments/{id}",
                method=HttpMethod.GET,
                data_source=DataSource.ORACLE_DB,
                expected_status_code=200,
            ),
        ],
        auth_header="Authorization",
        auth_token="Bearer test-token",
    )


class TestDotNetGenerator:
    def test_generates_suite(self, dotnet_service):
        gen = DotNetTestGenerator()
        suite = gen.generate_suite(dotnet_service)
        assert suite.name == "Regression Tests - CustomerService"
        assert len(suite.test_cases) > 0

    def test_generates_happy_path(self, dotnet_service):
        gen = DotNetTestGenerator()
        suite = gen.generate_suite(dotnet_service)
        happy = [t for t in suite.test_cases if "Happy Path" in t.name]
        assert len(happy) == 2

    def test_generates_invalid_id_for_path_params(self, dotnet_service):
        gen = DotNetTestGenerator()
        suite = gen.generate_suite(dotnet_service)
        invalid = [t for t in suite.test_cases if "Invalid ID" in t.name]
        assert len(invalid) == 1
        assert invalid[0].expected_status_code == 404

    def test_generates_unauthorized_test(self, dotnet_service):
        gen = DotNetTestGenerator()
        suite = gen.generate_suite(dotnet_service)
        unauth = [t for t in suite.test_cases if "Unauthorized" in t.name]
        assert len(unauth) == 2
        assert all(t.expected_status_code == 401 for t in unauth)

    def test_generates_db_performance_test(self, dotnet_service):
        gen = DotNetTestGenerator()
        suite = gen.generate_suite(dotnet_service)
        perf = [t for t in suite.test_cases if "DB Query" in t.name]
        assert len(perf) == 1
        assert "performance" in perf[0].tags

    def test_generates_external_service_test(self, dotnet_service):
        gen = DotNetTestGenerator()
        suite = gen.generate_suite(dotnet_service)
        ext = [t for t in suite.test_cases if "Resilience" in t.name]
        assert len(ext) == 1
        assert "external-service" in ext[0].tags

    def test_no_auth_tests_without_token(self):
        service = ServiceConfig(
            name="NoAuthService",
            service_type=ServiceType.DOTNET_CORE,
            base_url="http://localhost:5001",
            endpoints=[
                EndpointConfig(name="List", path="/api/items", method=HttpMethod.GET),
            ],
        )
        gen = DotNetTestGenerator()
        suite = gen.generate_suite(service)
        unauth = [t for t in suite.test_cases if "Unauthorized" in t.name]
        assert len(unauth) == 0


class TestSpringBootGenerator:
    def test_generates_suite(self, spring_service):
        gen = SpringBootTestGenerator()
        suite = gen.generate_suite(spring_service)
        assert suite.name == "Regression Tests - PaymentService"
        assert len(suite.test_cases) > 0

    def test_generates_actuator_health(self, spring_service):
        gen = SpringBootTestGenerator()
        suite = gen.generate_suite(spring_service)
        health = [t for t in suite.test_cases if "Actuator" in t.name]
        assert len(health) == 1
        assert health[0].full_url == "http://localhost:8080/actuator/health"

    def test_generates_not_found_test(self, spring_service):
        gen = SpringBootTestGenerator()
        suite = gen.generate_suite(spring_service)
        notfound = [t for t in suite.test_cases if "Not Found" in t.name]
        assert len(notfound) == 1
        assert notfound[0].expected_status_code == 404

    def test_includes_correct_tags(self, spring_service):
        gen = SpringBootTestGenerator()
        suite = gen.generate_suite(spring_service)
        for tc in suite.test_cases:
            assert "spring-boot" in tc.tags

    def test_builds_correct_urls(self, spring_service):
        gen = SpringBootTestGenerator()
        suite = gen.generate_suite(spring_service)
        happy = [t for t in suite.test_cases if "Happy Path" in t.name][0]
        assert happy.full_url == "http://localhost:8080/api/payments/{id}"
