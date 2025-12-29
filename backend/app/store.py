"""
In-memory storage for ConVerge
Simple dictionaries for fast access, no persistence
"""
from typing import Dict, List, Optional
from uuid import UUID
from .models import Conversation, ConversationNode, ConversationEdge


class InMemoryStore:
    """
    Global in-memory store for all conversations, nodes, and edges.
    Data is lost when the server restarts.
    """

    def __init__(self):
        self.conversations: Dict[UUID, Conversation] = {}
        self.nodes: Dict[UUID, ConversationNode] = {}
        self.edges: Dict[UUID, ConversationEdge] = {}

    # Conversation operations
    def create_conversation(self, conversation: Conversation) -> Conversation:
        """Store a new conversation"""
        self.conversations[conversation.id] = conversation
        return conversation

    def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)

    def list_conversations(self) -> List[Conversation]:
        """List all conversations, sorted by updated_at descending"""
        return sorted(
            self.conversations.values(),
            key=lambda c: c.updated_at,
            reverse=True
        )

    def delete_conversation(self, conversation_id: UUID) -> bool:
        """Delete conversation and all its nodes/edges"""
        if conversation_id not in self.conversations:
            return False

        # Delete all nodes belonging to this conversation
        nodes_to_delete = [
            node_id for node_id, node in self.nodes.items()
            if node.conversation_id == conversation_id
        ]
        for node_id in nodes_to_delete:
            del self.nodes[node_id]

        # Delete all edges connected to these nodes
        edges_to_delete = [
            edge_id for edge_id, edge in self.edges.items()
            if edge.source_node_id in nodes_to_delete or edge.target_node_id in nodes_to_delete
        ]
        for edge_id in edges_to_delete:
            del self.edges[edge_id]

        # Delete the conversation
        del self.conversations[conversation_id]
        return True

    # Node operations
    def create_node(self, node: ConversationNode) -> ConversationNode:
        """Store a new node"""
        self.nodes[node.id] = node
        return node

    def get_node(self, node_id: UUID) -> Optional[ConversationNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)

    def delete_node(self, node_id: UUID) -> bool:
        """Delete node and all its descendants"""
        if node_id not in self.nodes:
            return False

        # Find all descendants recursively
        def get_descendants(parent_id: UUID) -> List[UUID]:
            children = [
                node.id for node in self.nodes.values()
                if node.parent_id == parent_id
            ]
            descendants = children.copy()
            for child_id in children:
                descendants.extend(get_descendants(child_id))
            return descendants

        # Delete descendants first
        descendants = get_descendants(node_id)
        for desc_id in descendants:
            if desc_id in self.nodes:
                del self.nodes[desc_id]

        # Delete edges
        edges_to_delete = [
            edge_id for edge_id, edge in self.edges.items()
            if edge.source_node_id == node_id or edge.target_node_id == node_id
            or edge.source_node_id in descendants or edge.target_node_id in descendants
        ]
        for edge_id in edges_to_delete:
            del self.edges[edge_id]

        # Delete the node itself
        del self.nodes[node_id]
        return True

    def get_children(self, node_id: UUID) -> List[ConversationNode]:
        """Get all direct children of a node"""
        return [
            node for node in self.nodes.values()
            if node.parent_id == node_id
        ]

    def get_ancestors(self, node_id: UUID) -> List[ConversationNode]:
        """Get path from root to node (inclusive)"""
        path = []
        current_node = self.nodes.get(node_id)

        while current_node:
            path.insert(0, current_node)
            if current_node.parent_id:
                current_node = self.nodes.get(current_node.parent_id)
            else:
                break

        return path

    # Edge operations
    def create_edge(self, edge: ConversationEdge) -> ConversationEdge:
        """Store a new edge"""
        self.edges[edge.id] = edge
        return edge

    def get_edge(self, edge_id: UUID) -> Optional[ConversationEdge]:
        """Get edge by ID"""
        return self.edges.get(edge_id)

    def get_conversation_edges(self, conversation_id: UUID) -> List[ConversationEdge]:
        """Get all edges for a conversation"""
        node_ids = {
            node.id for node in self.nodes.values()
            if node.conversation_id == conversation_id
        }
        return [
            edge for edge in self.edges.values()
            if edge.source_node_id in node_ids
        ]

    def get_conversation_nodes(self, conversation_id: UUID) -> List[ConversationNode]:
        """Get all nodes for a conversation"""
        return [
            node for node in self.nodes.values()
            if node.conversation_id == conversation_id
        ]


# Global store instance
store = InMemoryStore()
