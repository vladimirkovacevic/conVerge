"""
In-memory data models for ConVerge
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class ConversationNode(BaseModel):
    """A node in the conversation graph"""
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    parent_id: Optional[UUID] = None

    # Core ConVerge data
    context: str  # Full materialized context
    response: Optional[str] = None  # LLM response
    query: Optional[str] = None  # User query that created this node

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ConversationEdge(BaseModel):
    """An edge connecting two nodes (represents a query transition)"""
    id: UUID = Field(default_factory=uuid4)
    source_node_id: UUID
    target_node_id: UUID
    query_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class Conversation(BaseModel):
    """A conversation containing a graph of nodes"""
    id: UUID = Field(default_factory=uuid4)
    title: str = "New Conversation"
    root_node_id: UUID
    active_node_id: UUID  # Currently selected node
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
