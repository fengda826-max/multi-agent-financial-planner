import pytest
import httpx
import asyncio

BASE_URL = "http://localhost:8000"


@pytest.mark.asyncio
async def test_health_check():
    """测试健康检查接口"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login():
    """测试注册和登录流程"""
    async with httpx.AsyncClient() as client:
        # 注册
        register_response = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": "testuser",
                "password": "testpassword123",
                "email": "test@example.com"
            }
        )
        assert register_response.status_code == 201

        # 登录
        login_response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

        return login_response.json()["access_token"]


@pytest.mark.asyncio
async def test_risk_assessment():
    """测试风险测评流程"""
    async with httpx.AsyncClient() as client:
        # 先登录获取token
        login_response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]

        # 提交风险测评
        assessment_response = await client.post(
            f"{BASE_URL}/api/risk-assessment",
            json={
                "age": 30,
                "income": 20000,
                "expenses": 12000,
                "risk_tolerance": "moderate",
                "investment_horizon": "5y"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert assessment_response.status_code == 200
        assert "risk_level" in assessment_response.json()


@pytest.mark.asyncio
async def test_full_planning_flow():
    """测试完整理财规划流程"""
    async with httpx.AsyncClient() as client:
        # 登录
        login_response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 提交风险测评
        await client.post(
            f"{BASE_URL}/api/risk-assessment",
            json={
                "age": 30,
                "income": 20000,
                "expenses": 12000,
                "risk_tolerance": "moderate",
                "investment_horizon": "5y"
            },
            headers=headers
        )

        # 启动理财规划
        planning_response = await client.post(
            f"{BASE_URL}/orchestrator/start",
            json={
                "user_id": "test-user-id",
                "risk_assessment": {
                    "age": 30,
                    "income": 20000,
                    "expenses": 12000,
                    "risk_tolerance": "moderate",
                    "investment_horizon": "5y"
                }
            },
            headers=headers
        )

        print(f"Planning response: {planning_response.status_code}")


if __name__ == "__main__":
    asyncio.run(test_health_check())
