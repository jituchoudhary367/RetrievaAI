import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from sqlalchemy import select
from db.models.connector import Connector
from tasks.connector_tasks import _get_sync_db, _get_fresh_token_sync
from connectors.google_drive.client import GoogleDriveClient
from connectors.google_drive.adapter import GoogleDriveConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("verify_parity")

async def main():
    engine, db = _get_sync_db()
    try:
        # Get a Google Drive connector
        connector = db.execute(select(Connector).where(Connector.provider == "google_drive").limit(1)).scalar_one_or_none()
        if not connector:
            logger.error("No Google Drive connector found in DB.")
            return

        logger.info(f"Found connector: {connector.id}")
        access_token = _get_fresh_token_sync(db, connector)

        # 1. Old Path
        logger.info("Running OLD path (GoogleDriveClient)...")
        old_client = GoogleDriveClient()
        old_file_ids = []
        page_token = None
        while True:
            result = await old_client.list_files(access_token, folder_id=connector.root_folder_id, page_token=page_token)
            old_file_ids.extend([f.file_id for f in result.files])
            if not result.has_more:
                break
            page_token = result.next_page_token

        # 2. New Path
        logger.info("Running NEW path (GoogleDriveConnector)...")
        new_adapter = GoogleDriveConnector()
        await new_adapter.authenticate({"access_token": access_token})
        new_file_ids = []
        async for f in new_adapter.full_sync():
            new_file_ids.append(f.external_id)

        # 3. Diff
        old_set = set(old_file_ids)
        new_set = set(new_file_ids)

        diff = old_set ^ new_set
        if diff:
            logger.error(f"PARITY FAILED! Mismatched IDs: {diff}")
            sys.exit(1)
        else:
            logger.info(f"PARITY SUCCESS! Both paths returned {len(old_set)} files exactly.")

        # Permissions check
        if old_file_ids:
            test_file = old_file_ids[0]
            logger.info(f"Checking permissions parity for file {test_file}...")
            # Assuming old path doesn't get permissions but we want to ensure new path doesn't crash
            perms = await new_adapter.get_permissions(test_file)
            logger.info(f"New path returned permissions: {perms}")
            
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
