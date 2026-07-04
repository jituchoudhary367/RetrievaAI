import asyncio
import httpx

async def test_ready():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        res = await client.get("/api/health/ready")
        print("Status:", res.status_code)
        print("Body:", res.text)

if __name__ == "__main__":
    asyncio.run(test_ready())
