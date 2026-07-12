import logging
from datetime import datetime, timezone
from sqlalchemy import select
from tasks.connector_tasks import _get_sync_db
from db.models.connector import Connector
from connectors.models import ConnectorStatusEnum
from connectors.tasks import discover_files_task, refresh_token_task

logger = logging.getLogger(__name__)

def evaluate_and_schedule_connectors() -> None:
    """
    Called periodically by Celery beat.
    Scans all connectors and schedules syncs or token refreshes as needed.
    """
    logger.info("Running automated connector scheduler...")
    engine, db = _get_sync_db()
    try:
        connectors = db.execute(
            select(Connector).where(
                Connector.status == ConnectorStatusEnum.CONNECTED.value,
                Connector.auto_sync == True
            )
        ).scalars().all()

        now = datetime.now(timezone.utc)

        for connector in connectors:
            try:
                _process_connector(connector, now)
            except Exception as e:
                logger.error(f"Error processing scheduler for connector {connector.id}: {e}", exc_info=True)
    finally:
        db.close()
        engine.dispose()

def _process_connector(connector: Connector, now: datetime) -> None:
    sync_state = connector.sync_state
    
    # 1. Check if we need to sync
    needs_sync = False
    if not sync_state or not sync_state.last_sync_completed_at:
        needs_sync = True
    else:
        elapsed = now - sync_state.last_sync_completed_at.replace(tzinfo=timezone.utc)
        if elapsed.total_seconds() > (connector.sync_interval_minutes * 60):
            needs_sync = True
            
    if needs_sync:
        logger.info(f"Scheduling auto-sync for connector {connector.id}")
        discover_files_task.delay(connector.id, is_incremental=True)

    # 2. Check if token needs refreshing
    cred = connector.credential
    if cred and cred.expires_at:
        time_to_expiry = cred.expires_at.replace(tzinfo=timezone.utc) - now
        if time_to_expiry.total_seconds() < (15 * 60) and cred.refresh_token:
            logger.info(f"Scheduling proactive token refresh for connector {connector.id}")
            refresh_token_task.delay(connector.id)
