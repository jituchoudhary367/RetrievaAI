import asyncio
import asyncpg
import urllib.parse
from dotenv import load_dotenv
import os

load_dotenv("backend/.env")

project_ref = "vwjspvouicqmgsqgqjse"
password = urllib.parse.quote_plus("Sup@b@se@2004")
host = "aws-1-ap-southeast-2.pooler.supabase.com"

# Test 1: Original (5432)
url1 = f"postgresql://postgres.{project_ref}:{password}@{host}:5432/postgres"
# Test 2: Transaction pool (6543)
url2 = f"postgresql://postgres.{project_ref}:{password}@{host}:6543/postgres"
# Test 3: No project ref in user (5432)
url3 = f"postgresql://postgres:{password}@{host}:5432/postgres"
# Test 4: aws-0 instead of aws-1
url4 = f"postgresql://postgres.{project_ref}:{password}@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres"
# Test 5: IPv6 direct (requires IPv6 support locally, usually fails on windows)
url5 = f"postgresql://postgres:{password}@{project_ref}.db.supabase.co:5432/postgres"


async def test_conn(name, url):
    print(f"Testing {name}: {url.replace(password, '***')}")
    try:
        conn = await asyncpg.connect(url, timeout=5)
        print(f"SUCCESS {name}")
        await conn.close()
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__} - {e}")

async def main():
    await test_conn("Test 1 (Original 5432)", url1)
    await test_conn("Test 2 (Transaction 6543)", url2)
    await test_conn("Test 3 (No project_ref)", url3)
    await test_conn("Test 4 (aws-0 pooler)", url4)
    await test_conn("Test 5 (IPv6 direct)", url5)

if __name__ == "__main__":
    asyncio.run(main())
