import asyncio
from sqlalchemy import text
from db.engine import async_engine

async def main():
    async with async_engine.begin() as conn:
        print("Starting user isolation migration...")

        # 1. Add user_id column (nullable initially)
        try:
            await conn.execute(text("ALTER TABLE documents ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)"))
            await conn.execute(text("ALTER TABLE conversation_messages ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)"))
            await conn.execute(text("ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)"))
            await conn.execute(text("ALTER TABLE query_events ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(36)"))
            await conn.execute(text("ALTER TABLE search_events ADD COLUMN IF NOT EXISTS temp_user_id VARCHAR(36)"))
            await conn.execute(text("ALTER TABLE search_click_events ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)"))
        except Exception as e:
            print(f"Error adding columns: {e}")

        # Backfill
        res = await conn.execute(text("SELECT id FROM users LIMIT 1"))
        admin_id = res.scalar()
        if not admin_id:
            print("No users found! Migration cannot set a default user_id.")
            return

        print(f"Using admin_id {admin_id} as fallback.")

        await conn.execute(text(f"UPDATE documents SET user_id = uploaded_by WHERE uploaded_by IS NOT NULL AND user_id IS NULL"))
        await conn.execute(text(f"UPDATE documents SET user_id = '{admin_id}' WHERE user_id IS NULL"))

        await conn.execute(text(f"""
            UPDATE conversation_messages 
            SET user_id = (SELECT user_id FROM conversations WHERE conversations.id = conversation_messages.conversation_id)
            WHERE user_id IS NULL
        """))

        await conn.execute(text(f"UPDATE ingestion_jobs SET user_id = '{admin_id}' WHERE user_id IS NULL"))

        await conn.execute(text(f"UPDATE query_events SET temp_user_id = COALESCE(user_id, '{admin_id}')"))
        await conn.execute(text("ALTER TABLE query_events DROP COLUMN IF EXISTS user_id"))
        await conn.execute(text("ALTER TABLE query_events RENAME COLUMN temp_user_id TO user_id"))

        await conn.execute(text(f"UPDATE search_events SET temp_user_id = COALESCE(user_id, '{admin_id}')"))
        await conn.execute(text("ALTER TABLE search_events DROP COLUMN IF EXISTS user_id CASCADE"))
        await conn.execute(text("ALTER TABLE search_events RENAME COLUMN temp_user_id TO user_id"))

        await conn.execute(text(f"""
            UPDATE search_click_events 
            SET user_id = (SELECT user_id FROM search_events WHERE search_events.id = search_click_events.search_event_id)
            WHERE user_id IS NULL
        """))
        await conn.execute(text(f"UPDATE search_click_events SET user_id = '{admin_id}' WHERE user_id IS NULL"))

        tables = [
            "documents", "conversation_messages", "ingestion_jobs", 
            "query_events", "search_events", "search_click_events"
        ]

        for table in tables:
            try:
                await conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN user_id SET NOT NULL"))
                await conn.execute(text(f"CREATE INDEX IF NOT EXISTS ix_{table}_user_id ON {table} (user_id)"))
                await conn.execute(text(f"ALTER TABLE {table} ADD CONSTRAINT fk_{table}_user_id FOREIGN KEY (user_id) REFERENCES users (id)"))
            except Exception as e:
                print(f"Constraint/index might already exist on {table}: {e}")

        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(main())
