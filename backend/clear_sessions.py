import asyncio
from db.engine import get_db
from db.models.user import UserSession
from sqlalchemy import delete

async def main():
    async for db in get_db():
        await db.execute(delete(UserSession))
        await db.commit()
        break
    print("Deleted all sessions.")

if __name__ == "__main__":
    asyncio.run(main())
