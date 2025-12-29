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
    logger.info("=" * 80)
    logger.info(f"📝 USER ACTION: Creating new conversation")
    logger.info(f"   Title: '{request.title}'")
    logger.info(f"   Initial context: {request.initial_context[:100]}..." if len(request.initial_context) > 100 else f"   Initial context: {request.initial_context}")
    logger.info(f"   Context length: {len(request.initial_context)} chars")

    # Create conversation
    conversation = Conversation(
        title=request.title,
        root_node_id=UUID(int=0),  # Temporary, will be updated
        active_node_id=UUID(int=0)
    )
    logger.info(f"   → Conversation ID: {conversation.id}")

    # Create root node
    root_node = ConversationNode(
        conversation_id=conversation.id,
        parent_id=None,
        context=request.initial_context,
        response=None,
        query=None
    )
    logger.info(f"   → Root node ID: {root_node.id}")

    # Update conversation with root node ID
    conversation.root_node_id = root_node.id
    conversation.active_node_id = root_node.id

    # Store in memory
    store.create_node(root_node)
    store.create_conversation(conversation)

    logger.info(f"✅ CONVERSATION CREATED:")
    logger.info(f"   - ID: {conversation.id}")
    logger.info(f"   - Title: {conversation.title}")
    logger.info(f"   - Root Node: {root_node.id}")
    logger.info("=" * 80)

    return CreateConversationResponse(
        conversation_id=conversation.id,
        root_node_id=root_node.id,
        active_node_id=conversation.active_node_id
    )


@router.get("", response_model=List[ConversationResponse])
async def list_conversations():
    """List all conversations"""
    logger.info("=" * 80)
    logger.info("📋 USER ACTION: Listing all conversations")
    conversations = store.list_conversations()

    # Auto-create default conversation if none exist
    if len(conversations) == 0:
        logger.info("   → No conversations found, creating default conversation...")

        # Create default conversation
        default_conversation = Conversation(
            title="Welcome to ConVerge",
            root_node_id=UUID(int=0),
            active_node_id=UUID(int=0)
        )

        # Create default root node with helpful context
        default_root_node = ConversationNode(
            conversation_id=default_conversation.id,
            parent_id=None,
            context="You are a helpful AI assistant. Assist the user with their questions and provide clear, concise answers.",
            response=None,
            query=None
        )

        # Update conversation with root node
        default_conversation.root_node_id = default_root_node.id
        default_conversation.active_node_id = default_root_node.id

        # Store in memory
        store.create_node(default_root_node)
        store.create_conversation(default_conversation)

        logger.info(f"   ✅ Created default conversation:")
        logger.info(f"      - ID: {default_conversation.id}")
        logger.info(f"      - Title: {default_conversation.title}")
        logger.info(f"      - Root Node: {default_root_node.id}")

        # Refresh conversation list
        conversations = store.list_conversations()

    logger.info(f"   → Returning {len(conversations)} conversation(s)")
    for conv in conversations:
        logger.info(f"      • {conv.title} (ID: {conv.id}, Active: {conv.active_node_id})")
    logger.info("=" * 80)
    return [ConversationResponse.model_validate(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: UUID):
    """Get conversation details"""
    logger.info("=" * 80)
    logger.info(f"🔍 USER ACTION: Getting conversation details")
    logger.info(f"   Conversation ID: {conversation_id}")
    conversation = store.get_conversation(conversation_id)
    if not conversation:
        logger.warning(f"❌ Conversation not found: {conversation_id}")
        logger.info("=" * 80)
        raise HTTPException(status_code=404, detail="Conversation not found")

    logger.info(f"✅ Found conversation:")
    logger.info(f"   - Title: {conversation.title}")
    logger.info(f"   - Root Node: {conversation.root_node_id}")
    logger.info(f"   - Active Node: {conversation.active_node_id}")
    logger.info("=" * 80)
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
    logger.info("=" * 80)
    logger.info(f"👆 USER ACTION: Switching active node")
    logger.info(f"   Conversation: {conversation_id}")
    logger.info(f"   New Active Node: {request.node_id}")

    conversation = store.get_conversation(conversation_id)
    if not conversation:
        logger.warning(f"❌ Conversation not found: {conversation_id}")
        logger.info("=" * 80)
        raise HTTPException(status_code=404, detail="Conversation not found")

    node = store.get_node(request.node_id)
    if not node:
        logger.warning(f"❌ Node not found: {request.node_id}")
        logger.info("=" * 80)
        raise HTTPException(status_code=404, detail="Node not found")

    if node.conversation_id != conversation_id:
        logger.warning(f"❌ Node {request.node_id} does not belong to conversation {conversation_id}")
        logger.info("=" * 80)
        raise HTTPException(status_code=400, detail="Node does not belong to this conversation")

    # Update active node
    old_active = conversation.active_node_id
    conversation.active_node_id = request.node_id
    conversation.updated_at = datetime.utcnow()

    logger.info(f"✅ NODE SWITCHED:")
    logger.info(f"   - Previous: {old_active}")
    logger.info(f"   - Current: {request.node_id}")
    logger.info(f"   - Node Query: {node.query if node.query else '(root node)'}")
    logger.info(f"   - Node Response: {node.response[:100] if node.response else '(no response yet)'}...")
    logger.info("=" * 80)

    return {"status": "selected", "active_node_id": str(request.node_id)}


@router.websocket("/{conversation_id}/stream")
async def websocket_stream(websocket: WebSocket, conversation_id: UUID):
    """WebSocket endpoint for streaming LLM responses"""
    logger.info("=" * 80)
    logger.info(f"🔌 WebSocket connection attempt for conversation: {conversation_id}")
    await websocket.accept()
    logger.info(f"✅ WebSocket accepted")

    try:
        conversation = store.get_conversation(conversation_id)
        if not conversation:
            logger.warning(f"❌ Conversation not found: {conversation_id}")
            logger.info("=" * 80)
            await websocket.send_json(StreamError(message="Conversation not found").model_dump())
            await websocket.close()
            return

        # Receive branch request
        data = await websocket.receive_json()
        request = BranchRequest(**data)

        logger.info(f"🤔 USER ACTION: New Query")
        logger.info(f"   Conversation: {conversation.title} ({conversation_id})")
        logger.info(f"   Query: \"{request.query}\"")
        logger.info(f"   Model: {request.model or 'auto (free models)'}")

        # Get parent node (use active if not specified)
        parent_id = request.parent_node_id or conversation.active_node_id
        parent_node = store.get_node(parent_id)

        if not parent_node:
            logger.warning(f"❌ Parent node not found: {parent_id}")
            logger.info("=" * 80)
            await websocket.send_json(StreamError(message="Parent node not found").model_dump())
            await websocket.close()
            return

        # Build context from ancestor path
        ancestors = store.get_ancestors(parent_id)
        logger.info(f"   → Building context from {len(ancestors)} ancestor node(s)")
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

        logger.info(f"   → Created new node: {new_node.id}")
        logger.info(f"   → Created edge: {parent_id} → {new_node.id}")

        # Update active node
        conversation.active_node_id = new_node.id
        conversation.updated_at = datetime.utcnow()

        # Stream response
        logger.info(f"   → Calling LLM for response...")
        logger.info(f"      System context: {ancestors[0].context[:80]}...")
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
            # Streaming in progress (tokens being sent via WebSocket)

        # Update node with complete response
        new_node.response = "".join(response_chunks)
        new_node.latency_ms = int((time.time() - start_time) * 1000)
        new_node.model = request.model or "auto-selected-free-model"

        # Log completion
        response_preview = new_node.response[:150].replace('\n', ' ') if new_node.response else '(empty)'
        logger.info(f"")
        logger.info(f"✅ RESPONSE COMPLETE:")
        logger.info(f"   - Tokens: {len(response_chunks)}")
        logger.info(f"   - Latency: {new_node.latency_ms}ms")
        logger.info(f"   - Response: \"{response_preview}...\"")
        logger.info(f"   - Node ID: {new_node.id}")
        logger.info("=" * 80)

        # Send completion
        await websocket.send_json(StreamComplete(
            node_id=str(new_node.id),  # Convert UUID to string
            metadata={
                "latency_ms": new_node.latency_ms,
                "model": new_node.model
            }
        ).model_dump())

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
