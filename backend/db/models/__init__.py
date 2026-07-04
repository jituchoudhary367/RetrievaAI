"""
db/models/__init__.py

Imports every ORM model so that SQLAlchemy's metadata knows about all tables
when `Base.metadata.create_all()` is called on startup.
"""

from db.models.user import User, UserSession
from db.models.invite import Invite
from db.models.auth_token import AuthToken
from db.models.telemetry import QueryEvent, QueryEventCitation, SearchEvent, SearchClickEvent
from db.models.ingestion import IngestionJob, IngestionJobLog
from db.models.document import Document
from db.models.tool import Tool, ToolExecution
from db.models.eval import EvalQuery, EvalRun
from db.models.settings import RuntimeSetting, UserPreference
from db.models.security import ApiKey
from db.models.audit import AuditLogEntry, Notification
from db.models.conversation import Conversation, ConversationMessage
from db.models.health import HealthSample

__all__ = [
    "User", "UserSession",
    "Invite", "AuthToken",
    "QueryEvent", "QueryEventCitation", "SearchEvent", "SearchClickEvent",
    "IngestionJob", "IngestionJobLog",
    "Document",
    "Tool", "ToolExecution",
    "EvalQuery", "EvalRun",
    "RuntimeSetting", "UserPreference",
    "ApiKey",
    "AuditLogEntry", "Notification",
    "Conversation", "ConversationMessage",
    "HealthSample",
]
