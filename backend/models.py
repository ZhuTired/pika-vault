from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from backend.database import Base

class CredentialType(str, enum.Enum):
    ACCOUNT = "account"
    DATABASE = "database"
    AI_LLM = "ai_llm"
    CLOUD = "cloud"
    DATA_WAREHOUSE = "data_warehouse"
    OTHER = "other"

class Credential(Base):
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False) # Store enum as string for simplicity
    tags = Column(JSON, default=[]) # List of strings
    fields = Column(JSON, nullable=False) # List of dicts: {"name": str, "value": str, "is_sensitive": bool}
    notes = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Boolean, default=False)

class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    url = Column(Text, nullable=False)
    favicon_url = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemConfig(Base):
    __tablename__ = "system_config"

    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=True) # JSON or simple string
