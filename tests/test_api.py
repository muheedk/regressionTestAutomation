import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.api.routes import store


@pytest.fixture(autouse=True)
def clear_store():
    store._services.clear()
    store._suites.clear()
    store._reports.clear()
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


SAMPLE_SERVICE = {
    "name": "TestService",
    "service_type": "dotnet_core",
    "base_url": "http://localhost:5001",
    "endpoints": [
        {
            "name": "Get Item",
            "path": "/api/items/{id}",
            "method": "GET",
            "data_source": "oracle_db",
            "expected_status_code": 200,
            "headers": [],
            "query_params": {},
        }
    ],
}


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestServiceEndpoints:
    @pytest.mark.asyncio
    async def test_create_service(self, client):
        resp = await client.post("/api/services", json=SAMPLE_SERVICE)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "TestService"
        assert data["id"]

    @pytest.mark.asyncio
    async def test_list_services(self, client):
        await client.post("/api/services", json=SAMPLE_SERVICE)
        resp = await client.get("/api/services")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_get_service(self, client):
        create_resp = await client.post("/api/services", json=SAMPLE_SERVICE)
        sid = create_resp.json()["id"]
        resp = await client.get(f"/api/services/{sid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "TestService"

    @pytest.mark.asyncio
    async def test_get_service_not_found(self, client):
        resp = await client.get("/api/services/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_service(self, client):
        create_resp = await client.post("/api/services", json=SAMPLE_SERVICE)
        sid = create_resp.json()["id"]
        resp = await client.delete(f"/api/services/{sid}")
        assert resp.status_code == 200

        resp = await client.get(f"/api/services/{sid}")
        assert resp.status_code == 404


class TestGenerationEndpoints:
    @pytest.mark.asyncio
    async def test_generate_tests(self, client):
        create_resp = await client.post("/api/services", json=SAMPLE_SERVICE)
        sid = create_resp.json()["id"]

        resp = await client.post(f"/api/generate/{sid}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["test_cases"]) > 0
        assert "Regression Tests" in data["name"]

    @pytest.mark.asyncio
    async def test_generate_not_found(self, client):
        resp = await client.post("/api/generate/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


class TestSuiteEndpoints:
    @pytest.mark.asyncio
    async def test_list_suites(self, client):
        create_resp = await client.post("/api/services", json=SAMPLE_SERVICE)
        sid = create_resp.json()["id"]
        await client.post(f"/api/generate/{sid}")

        resp = await client.get("/api/suites")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_delete_suite(self, client):
        create_resp = await client.post("/api/services", json=SAMPLE_SERVICE)
        sid = create_resp.json()["id"]
        gen_resp = await client.post(f"/api/generate/{sid}")
        suite_id = gen_resp.json()["id"]

        resp = await client.delete(f"/api/suites/{suite_id}")
        assert resp.status_code == 200
