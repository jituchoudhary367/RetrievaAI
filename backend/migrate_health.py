import asyncio
from sqlalchemy import text
from db.engine import async_engine

async def main():
    async with async_engine.begin() as conn:
        print("Starting ConnectorHealth migration...")
        try:
            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS connector_health (
                id VARCHAR(36) PRIMARY KEY,
                connector_id VARCHAR(36) NOT NULL,
                sampled_at TIMESTAMP WITH TIME ZONE NOT NULL,
                overall_status VARCHAR(50) NOT NULL DEFAULT 'healthy',
                oauth_expiry_minutes INTEGER,
                webhook_status VARCHAR(50),
                failed_files INTEGER NOT NULL DEFAULT 0,
                synced_files INTEGER NOT NULL DEFAULT 0,
                CONSTRAINT fk_connector_health_connector_id FOREIGN KEY (connector_id) REFERENCES connectors (id) ON DELETE CASCADE
            )
            """))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_connector_health_connector_id ON connector_health (connector_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_connector_health_sampled_at ON connector_health (sampled_at)"))
            print("Successfully created connector_health table.")
        except Exception as e:
            print(f"Migration error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
