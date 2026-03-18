from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from backend.models import CredentialType

# --- Shared ---
class TagList(BaseModel):
    tags: List[str]

class SortUpdate(BaseModel):
    id: int
    sort_order: int

# --- Credentials ---
class CredentialField(BaseModel):
    name: str
    value: str
    is_sensitive: bool = False

class CredentialBase(BaseModel):
    name: str
    type: CredentialType
    tags: List[str] = []
    fields: List[CredentialField]
    notes: Optional[str] = None
    sort_order: int = 0

class CredentialCreate(CredentialBase):
    pass

class CredentialUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[CredentialType] = None
    tags: Optional[List[str]] = None
    fields: Optional[List[CredentialField]] = None
    notes: Optional[str] = None
    sort_order: Optional[int] = None

class CredentialResponse(CredentialBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Bookmarks ---
class BookmarkBase(BaseModel):
    url: str
    category: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = 0

class BookmarkCreate(BookmarkBase):
    title: Optional[str] = None
    favicon_url: Optional[str] = None # Optional, can be auto-fetched

class BookmarkUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    favicon_url: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None

class BookmarkResponse(BookmarkBase):
    id: int
    title: str
    favicon_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Auth / Vault ---
class MasterPassword(BaseModel):
    password: str

class VaultStatus(BaseModel):
    is_initialized: bool
    is_unlocked: bool
