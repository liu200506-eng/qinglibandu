import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data


@pytest.mark.asyncio
async def test_root_endpoint(client):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "青藜伴读" in data["message"]


@pytest.mark.asyncio
async def test_resource_types(client):
    response = await client.get("/api/resources/types")
    assert response.status_code == 200
    data = response.json()
    assert "types" in data
    assert len(data["types"]) > 0


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post("/api/auth/register", json={
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_login_user(client):
    response = await client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code in [200, 401]


@pytest.mark.asyncio
async def test_profile_create(client):
    response = await client.post("/api/profile/create", json={
        "student_id": "test_student_1",
        "grade": "大一",
        "subject": "计算机网络"
    })
    assert response.status_code == 200
    data = response.json()
    assert "student_id" in data


@pytest.mark.asyncio
async def test_profile_get(client):
    response = await client.get("/api/profile/get/1")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_knowledge_tree(client):
    response = await client.get("/api/resources/knowledge-tree/computer_network")
    assert response.status_code == 200
    data = response.json()
    assert "tree" in data


@pytest.mark.asyncio
async def test_rag_health(client):
    response = await client.get("/api/rag/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_experiment_results(client):
    response = await client.get("/api/experiments/results")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_onboarding_status(client):
    response = await client.get("/api/tutoring/onboarding/status/1")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_plan_generate(client):
    response = await client.post("/api/plan/generate", json={
        "student_id": "1",
        "subject": "计算机网络"
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_generate_specific_resource_ppt(client):
    response = await client.post("/api/resources/generate/specific", json={
        "resource_type": "ppt",
        "topic": "TCP拥塞控制",
        "content": "TCP拥塞控制是计算机网络中的重要概念..."
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_generate_specific_resource_mindmap(client):
    response = await client.post("/api/resources/generate/specific", json={
        "resource_type": "mindmap",
        "topic": "HTTP协议",
        "content": "HTTP是应用层协议..."
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_generate_specific_resource_code(client):
    response = await client.post("/api/resources/generate/specific", json={
        "resource_type": "code",
        "topic": "Socket编程",
        "content": "Socket是网络编程的基础..."
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_generate_specific_resource_reading(client):
    response = await client.post("/api/resources/generate/specific", json={
        "resource_type": "reading",
        "topic": "网络安全",
        "content": "网络安全涉及加密、认证等技术..."
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_generate_specific_resource_video(client):
    response = await client.post("/api/resources/generate/specific", json={
        "resource_type": "video",
        "topic": "DNS解析",
        "content": "DNS负责域名到IP地址的解析..."
    })
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_resource_type(client):
    response = await client.post("/api/resources/generate/specific", json={
        "resource_type": "invalid_type",
        "topic": "测试",
        "content": "测试内容"
    })
    assert response.status_code == 200
    data = response.json()
    assert "error" in data["status"]


@pytest.mark.asyncio
async def test_feedback_submit(client):
    response = await client.post("/api/feedback/submit", json={
        "student_id": "1",
        "knowledge_point": "TCP",
        "rating": 5,
        "comment": "很好"
    })
    assert response.status_code == 200
