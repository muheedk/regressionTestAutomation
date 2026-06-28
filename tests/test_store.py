from uuid import uuid4

from app.core.test_store import TestStore
from app.models.service import (
    ExecutionReport,
    ServiceConfig,
    ServiceType,
    TestSuite,
)


class TestTestStore:
    def test_add_and_get_service(self):
        store = TestStore()
        service = ServiceConfig(
            name="Svc", service_type=ServiceType.DOTNET_CORE,
            base_url="http://localhost:5000", endpoints=[],
        )
        store.add_service(service)
        assert store.get_service(service.id) == service

    def test_get_all_services(self):
        store = TestStore()
        s1 = ServiceConfig(name="A", service_type=ServiceType.DOTNET_CORE, base_url="http://a", endpoints=[])
        s2 = ServiceConfig(name="B", service_type=ServiceType.JAVA_SPRING_BOOT, base_url="http://b", endpoints=[])
        store.add_service(s1)
        store.add_service(s2)
        assert len(store.get_all_services()) == 2

    def test_delete_service(self):
        store = TestStore()
        service = ServiceConfig(name="X", service_type=ServiceType.DOTNET_CORE, base_url="http://x", endpoints=[])
        store.add_service(service)
        assert store.delete_service(service.id)
        assert store.get_service(service.id) is None

    def test_delete_nonexistent(self):
        store = TestStore()
        assert not store.delete_service(uuid4())

    def test_add_and_get_suite(self):
        store = TestStore()
        service = ServiceConfig(name="S", service_type=ServiceType.DOTNET_CORE, base_url="http://s", endpoints=[])
        suite = TestSuite(name="Suite", service_config=service, test_cases=[])
        store.add_suite(suite)
        assert store.get_suite(suite.id) == suite

    def test_reports_sorted_by_date(self):
        from datetime import datetime
        store = TestStore()
        r1 = ExecutionReport(suite_name="Old", executed_at=datetime(2024, 1, 1))
        r2 = ExecutionReport(suite_name="New", executed_at=datetime(2024, 6, 1))
        store.add_report(r1)
        store.add_report(r2)
        reports = store.get_all_reports()
        assert reports[0].suite_name == "New"
