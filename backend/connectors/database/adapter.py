import logging
import asyncio
from typing import AsyncIterator, Dict, Any, List, Optional
import json

from connectors.base.connector import BaseConnector
from connectors.base.metadata import ConnectorFileMetadata
from connectors.base.sync import SyncCursor
from connectors.base.capabilities import CapabilitySet, Capability
from connectors.base.exceptions import ConnectorError, ConnectorAuthError

from .mapper import map_database_row, render_row_to_markdown

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


class DatabaseAdapter(BaseConnector):
    """
    Database Connector.
    Extracts rows from relational databases (PostgreSQL, MySQL, SQL Server, etc.)
    and maps them to searchable documents.
    """

    def __init__(self):
        self._connection_string: Optional[str] = None
        self._engine = None
        
        # Configuration for table and mapping
        self._table_name: str = ""
        self._pk_column: str = "id"
        self._watermark_column: Optional[str] = None
        self._mapping_config: Dict[str, Any] = {}

    @property
    def provider_name(self) -> str:
        return "database"

    def capabilities(self) -> CapabilitySet:
        return {
            Capability.API_KEY_AUTH,
            Capability.INCREMENTAL_SYNC,
            Capability.METADATA_EXTRACTION,
        }

    async def authenticate(self, credentials: Dict[str, Any]) -> None:
        if not SQLALCHEMY_AVAILABLE:
            raise ConnectorError("SQLAlchemy is not installed")
            
        self._connection_string = credentials.get("connection_string")
        if not self._connection_string:
            raise ConnectorAuthError("DatabaseAdapter requires 'connection_string'")
            
        self._table_name = credentials.get("table_name", "")
        if not self._table_name:
            raise ConnectorAuthError("DatabaseAdapter requires 'table_name'")
            
        self._pk_column = credentials.get("pk_column", "id")
        self._watermark_column = credentials.get("watermark_column")
        self._mapping_config = credentials.get("mapping_config", {})
        
        try:
            self._engine = create_engine(self._connection_string)
        except Exception as e:
            raise ConnectorAuthError(f"Failed to create database engine: {e}")

    async def get_auth_url(self, state: str) -> str:
        raise ConnectorError("Database uses connection string, not OAuth")

    async def exchange_code(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        raise ConnectorError("Database uses connection string, not OAuth")

    async def refresh_token(self, refresh_token_str: str) -> Dict[str, Any]:
        return {}

    async def revoke_token(self, token: str) -> None:
        pass

    async def health_check(self) -> Dict[str, Any]:
        if not self._engine:
            return {"status": "error", "message": "Not authenticated"}
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _fetch_rows(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Synchronous fetch to be run in a thread"""
        with self._engine.connect() as conn:
            result = conn.execute(text(query), params)
            # Use _mapping to get dictionary-like access
            return [dict(row._mapping) for row in result]

    async def full_sync(self) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._engine:
            raise ConnectorAuthError("Not authenticated")

        query = f"SELECT * FROM {self._table_name}"
        # We can implement pagination here if needed, but for now we fetch all
        # or fetch in chunks. A robust implementation would chunk by PK.
        rows = await asyncio.to_thread(self._fetch_rows, query, {})
        
        for row in rows:
            yield map_database_row(row, self._table_name, self._pk_column, self._mapping_config)

    async def incremental_sync(self, cursor: SyncCursor) -> AsyncIterator[ConnectorFileMetadata]:
        if not self._engine:
            raise ConnectorAuthError("Not authenticated")
            
        if not self._watermark_column:
            # Fallback to full sync if no watermark is defined
            async for item in self.full_sync():
                yield item
            return
            
        last_watermark = cursor.token if cursor else None
        
        if last_watermark:
            query = f"SELECT * FROM {self._table_name} WHERE {self._watermark_column} > :watermark ORDER BY {self._watermark_column} ASC"
            params = {"watermark": last_watermark}
        else:
            query = f"SELECT * FROM {self._table_name} ORDER BY {self._watermark_column} ASC"
            params = {}
            
        rows = await asyncio.to_thread(self._fetch_rows, query, params)
        
        max_watermark = last_watermark
        for row in rows:
            val = row.get(self._watermark_column)
            if val:
                # Convert to string to store in cursor
                str_val = str(val)
                if not max_watermark or str_val > max_watermark:
                    max_watermark = str_val
                    
            yield map_database_row(row, self._table_name, self._pk_column, self._mapping_config)
            
        if cursor and max_watermark:
            cursor.token = max_watermark

    async def detect_deletes(self, cursor: SyncCursor) -> AsyncIterator[str]:
        # SQL incremental sync typically handles inserts/updates via a watermark.
        # Hard deletes require a tombstone table, change data capture (CDC), or full sync comparison.
        # We leave this empty unless a tombstone query is configured.
        for x in []:
            yield x

    async def download_file(self, file_id: str) -> bytes:
        """
        Download file content. For databases, this means rendering the row to markdown.
        Since we don't have the row data here directly, we must re-fetch it from the DB.
        """
        if not self._engine:
            raise ConnectorAuthError("Not authenticated")

        if not file_id.startswith("db://"):
            raise ConnectorError(f"Invalid database file_id: {file_id}")
            
        # file_id is db://table_name/pk_val
        parts = file_id[5:].split("/")
        if len(parts) < 2:
            raise ConnectorError(f"Invalid database file_id format: {file_id}")
            
        table_name = parts[0]
        pk_val = parts[1]
        
        query = f"SELECT * FROM {table_name} WHERE {self._pk_column} = :pk"
        rows = await asyncio.to_thread(self._fetch_rows, query, {"pk": pk_val})
        
        if not rows:
            raise ConnectorError(f"Row not found for pk {pk_val}")
            
        markdown = render_row_to_markdown(rows[0], self._mapping_config)
        return markdown.encode("utf-8")

    async def get_permissions(self, file_id: str) -> List[Dict[str, Any]]:
        return []
