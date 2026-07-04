import asyncio
from db.engine import async_session_factory
from db.models.document import Document
from sqlalchemy import select
from pathlib import Path

async def main():
    async with async_session_factory() as db:
        result = await db.execute(select(Document).where(Document.title == "Untitled"))
        docs = result.scalars().all()
        for doc in docs:
            if doc.source:
                doc.title = Path(doc.source).name
                print(f"Updated document {doc.id} title to {doc.title}")
        await db.commit()

if __name__ == "__main__":
    asyncio.run(main())
