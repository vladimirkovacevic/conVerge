"""
Node API endpoints
"""
from fastapi import APIRouter, HTTPException
from uuid import UUID
from typing import List

from ..store import store
from ..schemas import NodeResponse

router = APIRouter(prefix="/api/nodes", tags=["nodes"])


@router.get("/{node_id}", response_model=NodeResponse)
async def get_node(node_id: UUID):
    """Get node details"""
    node = store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    return NodeResponse.model_validate(node)


@router.delete("/{node_id}")
async def delete_node(node_id: UUID):
    """Delete a node and all its descendants"""
    node = store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Cannot delete root node
    if node.parent_id is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete root node. Delete the conversation instead."
        )

    success = store.delete_node(node_id)
    return {"status": "deleted", "node_id": str(node_id)}


@router.get("/{node_id}/ancestors", response_model=List[NodeResponse])
async def get_ancestors(node_id: UUID):
    """Get all ancestor nodes from root to this node"""
    node = store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    ancestors = store.get_ancestors(node_id)
    return [NodeResponse.model_validate(n) for n in ancestors]


@router.get("/{node_id}/children", response_model=List[NodeResponse])
async def get_children(node_id: UUID):
    """Get all direct children of a node"""
    node = store.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    children = store.get_children(node_id)
    return [NodeResponse.model_validate(n) for n in children]
