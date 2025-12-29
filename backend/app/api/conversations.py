"""
Conversation API endpoints
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from uuid import UUID
from typing import List
from datetime import datetime
import time
import logging

from ..store import store
from ..models import Conversation, ConversationNode, ConversationEdge
from ..services.llm import get_llm_client
from ..schemas import (
    CreateConversationRequest,
    CreateConversationResponse,
    ConversationResponse,
    GraphResponse,
    NodeResponse,
    EdgeResponse,
    SelectNodeRequest,
    BranchRequest,
    StreamToken,
    StreamComplete,
    StreamError
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("", response_model=CreateConversationResponse)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation with initial root node"""
    logger.info(f"📝 Creating new conversation: '{request.title}'")
    logger.info(f"   Initial context length: {len(request.initial_context)} chars")

    # Create conversation
    conversation = Conversation(
        title=request.title,
        root_node_id=UUID(int=0),  # Temporary, will be updated
        active_node_id=UUID(int=0)
    )
    logger.info(f"   Conversation ID: {conversation.id}")

    # Create root node
    root_node = ConversationNode(
        conversation_id=conversation.id,
        parent_id=None,
        context=request.initial_context,
        response=None,
        query=None
    )
    logger.info(f"   Root node ID: {root_node.id}")

    # Update conversation with root node ID
    conversation.root_node_id = root_node.id
    conversation.active_node_id = root_node.id

    # Store in memory
    store.create_node(root_node)
    store.create_conversation(conversation)
    logger.info(f"✅ Conversation created successfully: {conversation.id}")

    return CreateConversationResponse(
        conversation_id=conversation.id,
        root_node_id=root_node.id,
        active_node_id=conversation.active_node_id
    )


@router.get("", response_model=List[ConversationResponse])
async def list_conversations():
    """List all conversations"""
    logger.info("📋 Listing all conversations")
    conversations = store.list_conversations()
    logger.info(f"   Found {len(conversations)} conversations")
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: UUID):
    """Get conversation details"""
    logger.info(f"🔍 Getting conversation: {conversation_id}")
    conversation = store.get_conversation(conversation_id)
    if not conversation:
        logger.warning(f"❌ Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

    logger.info(f"✅ Found conversation: '{conversation.title}'")
    return ConversationResponse.model_validate(conversation)


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: UUID):
    """Delete a conversation and all its nodes"""
    logger.info(f"🗑️ Deleting conversation: {conversation_id}")
    success = store.delete_conversation(conversation_id)
    if not success:
        logger.warning(f"❌ Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

    logger.info(f"✅ Conversation deleted: {conversation_id}")
    return {"status": "deleted", "conversation_id": str(conversation_id)}


@router.get("/{conversation_id}/graph", response_model=GraphResponse)
async def get_conversation_graph(conversation_id: UUID):
    """Get the full graph structure for a conversation"""
    logger.info(f"🌳 Getting graph for conversation: {conversation_id}")
    conversation = store.get_conversation(conversation_id)
    if not conversation:
        logger.warning(f"❌ Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

    nodes = store.get_conversation_nodes(conversation_id)
    edges = store.get_conversation_edges(conversation_id)
    logger.info(f"   Found {len(nodes)} nodes and {len(edges)} edges")

    # Convert to response format
    node_responses = [NodeResponse.model_validate(n) for n in nodes]
    edge_responses = [
        EdgeResponse(
            id=e.id,
            source=e.source_node_id,  # Map to 'source' for React Flow
            target=e.target_node_id,  # Map to 'target' for React Flow
            query_text=e.query_text,
            created_at=e.created_at
        )
        for e in edges
    ]

    logger.info(f"✅ Graph data prepared for {conversation_id}")
    return GraphResponse(
        conversation_id=conversation_id,
        active_node_id=conversation.active_node_id,
        nodes=node_responses,
        edges=edge_responses
    )


@router.post("/{conversation_id}/select")
async def select_node(conversation_id: UUID, request: SelectNodeRequest):
    """Select a node as active in the conversation"""
    logger.info(f"👆 Selecting node {request.node_id} in conversation {conversation_id}")
    conversation = store.get_conversation(conversation_id)
    if not conversation:
        logger.warning(f"❌ Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

    node = store.get_node(request.node_id)
    if not node:
        logger.warning(f"❌ Node not found: {request.node_id}")
        raise HTTPException(status_code=404, detail="Node not found")

    if node.conversation_id != conversation_id:
        logger.warning(f"❌ Node {request.node_id} does not belong to conversation {conversation_id}")
        raise HTTPException(status_code=400, detail="Node does not belong to this conversation")

    # Update active node
    conversation.active_node_id = request.node_id
    conversation.updated_at = datetime.utcnow()
    logger.info(f"✅ Node selected: {request.node_id}")

    return {"status": "selected", "active_node_id": str(request.node_id)}


@router.websocket("/{conversation_id}/stream")
async def websocket_stream(websocket: WebSocket, conversation_id: UUID):
    """WebSocket endpoint for streaming LLM responses"""
    logger.info(f"🔌 WebSocket connection attempt for conversation: {conversation_id}")
    await websocket.accept()
    logger.info(f"✅ WebSocket accepted for conversation: {conversation_id}")

    try:
        conversation = store.get_conversation(conversation_id)
        if not conversation:
            logger.info(f"❌ Conversation not found: {conversation_id}")
            await websocket.send_json(StreamError(message="Conversation not found").model_dump())
            await websocket.close()
            return
        logger.info(f"✅ Found conversation: {conversation.title}")

        # Receive branch request
        logger.info("📥 Waiting for branch request...")
        data = await websocket.receive_json()
        logger.info(f"📥 Received data: {data}")
        request = BranchRequest(**data)
        logger.info(f"✅ Parsed request - query: '{request.query}', model: {request.model}")

        # Get parent node (use active if not specified)
        parent_id = request.parent_node_id or conversation.active_node_id
        logger.info(f"📍 Parent node ID: {parent_id}")
        parent_node = store.get_node(parent_id)

        if not parent_node:
            logger.info(f"❌ Parent node not found: {parent_id}")
            await websocket.send_json(StreamError(message="Parent node not found").model_dump())
            await websocket.close()
            return
        logger.info(f"✅ Found parent node")

        # Build context from ancestor path
        logger.info("🔍 Building context from ancestors...")
        ancestors = store.get_ancestors(parent_id)
        logger.info(f"📚 Found {len(ancestors)} ancestors")
        context_parts = [ancestors[0].context]  # Start with root context

        for ancestor in ancestors[1:]:
            if ancestor.query and ancestor.response:
                context_parts.append(f"User: {ancestor.query}")
                context_parts.append(f"Assistant: {ancestor.response}")

        # Add current query
        context_parts.append(f"User: {request.query}")
        full_context = "\n\n".join(context_parts)

        # Create new node
        new_node = ConversationNode(
            conversation_id=conversation_id,
            parent_id=parent_id,
            context=full_context,
            response="",  # Will be filled as we stream
            query=request.query,
            model=request.model
        )

        # Create edge
        edge = ConversationEdge(
            source_node_id=parent_id,
            target_node_id=new_node.id,
            query_text=request.query
        )

        # Store node and edge
        store.create_node(new_node)
        store.create_edge(edge)

        # Update active node
        conversation.active_node_id = new_node.id
        conversation.updated_at = datetime.utcnow()

        # Stream response
        logger.info("🤖 Starting LLM streaming...")
        logger.info(f"   Requested model: {request.model} (will try free models if this fails)")
        logger.info(f"   System context: {ancestors[0].context[:100]}...")
        start_time = time.time()
        response_chunks = []
        successful_model = None

        async for token in get_llm_client().stream_response(
            context=ancestors[0].context,  # Use root context as system prompt
            query=f"{chr(10).join(context_parts[1:])}\n\nUser: {request.query}".strip(),
            model=None  # Pass None to try all free models in sequence
        ):
            response_chunks.append(token)
            await websocket.send_json(StreamToken(content=token).model_dump())
            logger.info(".", end="", flush=True)  # Show streaming progress

        # Update node with complete response
        logger.info()  # New line after streaming dots
        new_node.response = "".join(response_chunks)
        new_node.latency_ms = int((time.time() - start_time) * 1000)
        logger.info(f"✅ Streaming complete - {len(response_chunks)} tokens in {new_node.latency_ms}ms")

        # Store which model was actually used (will be set by LLM client)
        # For now, keep the requested model in metadata
        new_node.model = request.model or "auto-selected-free-model"

        # Send completion
        await websocket.send_json(StreamComplete(
            node_id=str(new_node.id),  # Convert UUID to string
            metadata={
                "latency_ms": new_node.latency_ms,
                "model": new_node.model
            }
        ).model_dump())
        logger.info(f"📤 Sent completion message")

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected by client")
        pass
    except Exception as e:
        logger.info(f"❌ Error in WebSocket handler: {e}")
        import traceback
        traceback.print_exc()
        try:
            await websocket.send_json(StreamError(message=str(e)).model_dump())
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
