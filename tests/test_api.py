"""
Integration tests for the DevBrain API.
Uses an in-memory SQLite database for isolation.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    from app.models import user, event, skill  # noqa: F401

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    """Register a test user and return auth headers."""
    resp = await client.post("/api/auth/register", json={
        "email": "test@devbrain.dev",
        "username": "testuser",
        "password": "securepass123",
        "full_name": "Test User",
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─── Auth Tests ──────────────────────────────────────────────────────────────

class TestAuth:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={
            "email": "newuser@devbrain.dev",
            "username": "newuser",
            "password": "password123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert data["username"] == "newuser"

    async def test_register_duplicate_email(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/auth/register", json={
            "email": "test@devbrain.dev",
            "username": "other",
            "password": "password123",
        })
        assert resp.status_code == 400

    async def test_get_profile(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    async def test_unauthorized_access(self, client: AsyncClient):
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401


# ─── Events Tests ─────────────────────────────────────────────────────────────

class TestEvents:
    async def test_ingest_event(self, client: AsyncClient, auth_headers):
        resp = await client.post("/api/events/", headers=auth_headers, json={
            "topic": "React Hooks",
            "domain": "Frontend",
            "technology": "React",
            "concept": "useEffect",
            "source": "browser",
            "depth": "intermediate",
            "confidence_score": 0.8,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["topic"] == "React Hooks"
        assert data["technology"] == "React"

    async def test_list_events_empty(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/events/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_list_events_after_ingest(self, client: AsyncClient, auth_headers):
        await client.post("/api/events/", headers=auth_headers, json={
            "topic": "FastAPI", "domain": "Backend", "technology": "FastAPI",
            "source": "manual", "depth": "beginner", "confidence_score": 0.6,
        })
        resp = await client.get("/api/events/", headers=auth_headers)
        assert resp.json()["total"] == 1


# ─── Skills Tests ─────────────────────────────────────────────────────────────

class TestSkills:
    async def _seed_events(self, client, headers):
        events = [
            {"topic": "React Hooks", "domain": "Frontend", "technology": "React", "source": "browser", "depth": "intermediate", "confidence_score": 0.9},
            {"topic": "TypeScript Generics", "domain": "Frontend", "technology": "TypeScript", "source": "manual", "depth": "advanced", "confidence_score": 0.85},
            {"topic": "FastAPI Routing", "domain": "Backend", "technology": "FastAPI", "source": "manual", "depth": "beginner", "confidence_score": 0.7},
        ]
        for e in events:
            await client.post("/api/events/", headers=headers, json=e)

    async def test_skill_graph_empty(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/skills/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_skills"] == 0
        assert data["overall_score"] == 0.0

    async def test_skill_graph_after_events(self, client: AsyncClient, auth_headers):
        await self._seed_events(client, auth_headers)
        resp = await client.get("/api/skills/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_skills"] > 0
        domains = [d["domain"] for d in data["domains"]]
        assert "Frontend" in domains
        assert "Backend" in domains

    async def test_gaps_endpoint(self, client: AsyncClient, auth_headers):
        await self._seed_events(client, auth_headers)
        resp = await client.get("/api/skills/gaps", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "gaps" in data
        assert "total_gaps" in data


# ─── Dashboard Tests ──────────────────────────────────────────────────────────

class TestDashboard:
    async def test_dashboard(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/dashboard/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert "stats" in data
        assert "activity_last_30_days" in data


# ─── Recommendations Tests ────────────────────────────────────────────────────

class TestRecommendations:
    async def test_recommendations_empty(self, client: AsyncClient, auth_headers):
        resp = await client.get("/api/recommendations/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "weekly_focus" in data
        assert "explore_next" in data
        assert "quick_wins" in data

    async def test_health(self, client: AsyncClient):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
