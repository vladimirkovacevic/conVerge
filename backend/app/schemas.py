"""
API request/response schemas
"""
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime


# Request schemas
class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    initial_context: str = "You are a helpful AI assistant."


class BranchRequest(BaseModel):
    query: str
    model: Optional[str] = None
    parent_node_id: Optional[UUID] = None  # If None, use active node


class SelectNodeRequest(BaseModel):
    node_id: UUID


# Response schemas
class NodeResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    parent_id: Optional[UUID]
    context: str
    response: Optional[str]
    query: Optional[str]
    created_at: datetime
    model: Optional[str]
    tokens_used: Optional[int]
    latency_ms: Optional[int]

    class Config:
        from_attributes = True


class EdgeResponse(BaseModel):
    id: UUID
    source: UUID  # Renamed from source_node_id for React Flow compatibility
    target: UUID  # Renamed from target_node_id for React Flow compatibility
    query_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: UUID
    title: str
    root_node_id: UUID
    active_node_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    conversation_id: UUID
    active_node_id: UUID
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]


class CreateConversationResponse(BaseModel):
    conversation_id: UUID
    root_node_id: UUID
    active_node_id: UUID


# WebSocket message types
class StreamToken(BaseModel):
    type: str = "token"
    content: str

    class Config:
        json_encoders = {UUID: str}


class StreamComplete(BaseModel):
    type: str = "complete"
    node_id: str  # Changed from UUID to str for JSON serialization
    metadata: dict

    class Config:
        json_encoders = {UUID: str}


class StreamError(BaseModel):
    type: str = "error"
    message: str
