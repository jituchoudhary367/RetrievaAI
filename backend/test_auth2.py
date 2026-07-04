import asyncio
import httpx
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_auth():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. Signup
        print("Signing up...")
        res = await client.post("/api/signup", json={
            "email": "test401@example.com",
            "password": "Password123!",
            "tenant_name": "Test 401 Tenant"
        })
        print(f"Signup: {res.status_code} {res.text}")
        
        # 2. Login
        print("\nLogging in...")
        res = await client.post("/api/login", json={
            "email": "test401@example.com",
            "password": "Password123!"
        })
        print(f"Login: {res.status_code}")
        
        if res.status_code != 200:
            print(res.text)
            return
            
        data = res.json()
        token = data.get("access_token")
        print(f"Got token: {token[:20]}...")
        
        # 3. Hit an authenticated endpoint
        print("\nFetching notifications...")
        res = await client.get("/api/notifications", headers={
            "Authorization": f"Bearer {token}"
        })
        print(f"Notifications: {res.status_code} {res.text}")

if __name__ == "__main__":
    asyncio.run(test_auth())
