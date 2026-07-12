import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from tasks.connector_tasks import _get_sync_db
from db.models.connector import Connector, ConnectorHealth, ConnectorFile, ConnectorCredential

logger = logging.getLogger(__name__)

class HealthMonitor:
    @staticmethod
    def check(connector_id: str) -> dict:
        """
        Evaluate the health of a connector and write to connector_health.
        Returns the sampled metrics as a dict.
        """
        engine, db = _get_sync_db()
        try:
            connector = db.get(Connector, connector_id)
            if not connector:
                return {}
            
            # Gather metrics
            now = datetime.now(timezone.utc)
            oauth_expiry_minutes = None
            if connector.credential and connector.credential.expires_at:
                diff = connector.credential.expires_at.replace(tzinfo=timezone.utc) - now
                oauth_expiry_minutes = int(diff.total_seconds() / 60)
            
            failed_files = db.execute(
                select(func.count(ConnectorFile.id)).where(
                    ConnectorFile.connector_id == connector_id,
                    ConnectorFile.sync_status == "failed"
                )
            ).scalar() or 0
            
            synced_files = db.execute(
                select(func.count(ConnectorFile.id)).where(
                    ConnectorFile.connector_id == connector_id,
                    ConnectorFile.sync_status == "synced"
                )
            ).scalar() or 0
            
            webhook_status = "inactive"
            if connector.sync_state and connector.sync_state.webhook_channel_id:
                webhook_status = "active"
                
            overall_status = "healthy"
            if connector.status == "error" or failed_files > 0:
                overall_status = "degraded"
            if oauth_expiry_minutes is not None and oauth_expiry_minutes < 0:
                overall_status = "unhealthy"

            # Create sample
            sample = ConnectorHealth(
                connector_id=connector_id,
                overall_status=overall_status,
                oauth_expiry_minutes=oauth_expiry_minutes,
                webhook_status=webhook_status,
                failed_files=failed_files,
                synced_files=synced_files,
            )
            db.add(sample)
            db.commit()
            
            return {
                "overall_status": overall_status,
                "oauth_expiry_minutes": oauth_expiry_minutes,
                "webhook_status": webhook_status,
                "failed_files": failed_files,
                "synced_files": synced_files,
            }
        finally:
            db.close()
            engine.dispose()
