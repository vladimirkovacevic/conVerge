# ConVerge Implementation Plan (Simplified)

## Executive Summary

This document outlines a **simplified** technical implementation plan for **ConVerge**, a graph-based framework for user-controlled conversational context management. The system uses **in-memory storage** for rapid development and a beautiful UI for an excellent user experience.

**Status:** 🟢 Ready to Build
**Last Updated:** 2025-12-29
**Architecture:** In-Memory (session-based, data resets on restart)

---

## 1. System Architecture

### 1.1 Simplified High-Level Architecture

```
┌─────────────────────┐
│   Frontend UI       │ ← React + React Flow (beautiful graph viz)
└──────────┬──────────┘
           │ REST API + WebSocket
┌──────────▼──────────┐
│   Backend API       │ ← FastAPI (Python)
│   ┌─────────────┐   │
│   │ In-Memory   │   │ ← Python dicts/lists (session storage)
│   │ Storage     │   │
│   └─────────────┘   │
│   ┌─────────────┐   │
│   │ LLM Client  │   │ ← OpenRouter API integration
│   └─────────────┘   │
└─────────────────────┘
```

### 1.2 Component Breakdown

1. **Frontend Layer**
   - Beautiful graph visualization with React Flow
   - Smooth animations and transitions
   - Node/edge interaction controls
   - Context viewer with syntax highlighting
   - Real-time streaming responses

2. **Backend API Layer**
   - FastAPI with in-memory data structures
   - RESTful endpoints for graph operations
   - WebSocket for streaming LLM responses
   - Simple session management

3. **Data Layer**
   - Python dictionaries and lists
   - Tree traversal algorithms
   - No persistence (fresh start each session)

4. **LLM Integration Layer**
   - OpenRouter API client
   - Streaming support
   - Multiple free model options

---

## 2. Technology Stack

### 2.1 Frontend (Beautiful & Modern)

| Component | Technology | Why | Version Notes |
|-----------|-----------|-----|---------------|
| Framework | **React 18** + TypeScript | Type safety, excellent ecosystem | React 18.2+ |
| Graph UI | **React Flow v11** | Beautiful, interactive node graphs | **Important:** v11 has different exports than v10 |
| State | **Zustand** | Simple, minimal boilerplate | Used by React Flow internally |
| UI Components | **Tailwind CSS v3.4.1** | Utility-first CSS | **Use v3, not v4** - v4 has breaking changes |
| API Client | **TanStack Query v5** | Caching, real-time updates | Perfect for real-time graph updates |
| Build Tool | **Vite 7** | Lightning fast dev experience | Hot reload for components |
| Icons | **Lucide React** | Beautiful, consistent icons | Optional but recommended |

### 2.2 Backend (Simple & Fast)

| Component | Technology | Why |
|-----------|-----------|-----|
| Framework | **FastAPI** | Async, auto-docs, type hints |
| Validation | **Pydantic v2** | Built-in validation |
| HTTP Client | **httpx** | Async OpenRouter client |
| Storage | **Python dicts** | In-memory, zero setup |

### 2.3 LLM Integration

**Primary: OpenRouter API with Automatic Fallback**

**Critical:** OpenRouter free models have availability issues. **Implement model iteration** - try models sequentially until one succeeds.

- **Tested Free Models (in priority order):**
  1. `meta-llama/llama-3.3-70b-instruct:free` - Best quality when available
  2. `meta-llama/llama-3.2-3b-instruct:free` - Fast, reliable
  3. `amazon/nova-2-lite-v1:free` - Good fallback
  4. `openai/gpt-oss-20b:free` - Experimental
  5. `google/gemma-3-27b-it:free` - Alternative option
  6. `mistralai/mistral-7b-instruct:free` - Solid performer
  7. `nvidia/nemotron-nano-9b-v2:free` - Specialized
  8. `alibaba/tongyi-deepresearch-30b-a3b:free` - Research tasks
  9. `moonshotai/kimi-k2:free` - Long context

**Implementation:** Try each model in order. If one returns 404 or error, automatically try the next.

---

## 3. Data Models (In-Memory)

### 3.1 Simple Python Data Structures

```python
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel

# In-Memory Storage
class InMemoryStore:
    """Single global store for all data"""
    conversations: dict[UUID, 'Conversation'] = {}
    nodes: dict[UUID, 'ConversationNode'] = {}
    edges: dict[UUID, 'ConversationEdge'] = {}

# Data Models
class ConversationNode(BaseModel):
    id: UUID = uuid4()
    conversation_id: UUID
    parent_id: Optional[UUID] = None

    # Core ConVerge data
    context: str  # Full materialized context
    response: Optional[str] = None  # LLM response
    query: Optional[str] = None  # User query that created this

    # Metadata
    created_at: datetime = datetime.utcnow()
    model: Optional[str] = None
    tokens_used: Optional[int] = None

    # Tree navigation helpers
    def get_path(self) -> list[UUID]:
        """Get path from root to this node"""
        path = [self.id]
        node = self
        while node.parent_id:
            node = InMemoryStore.nodes[node.parent_id]
            path.insert(0, node.id)
        return path

    def get_children(self) -> list['ConversationNode']:
        """Get all child nodes"""
        return [n for n in InMemoryStore.nodes.values()
                if n.parent_id == self.id]

class ConversationEdge(BaseModel):
    id: UUID = uuid4()
    source_node_id: UUID
    target_node_id: UUID
    query_text: str
    created_at: datetime = datetime.utcnow()

class Conversation(BaseModel):
    id: UUID = uuid4()
    title: str = "New Conversation"
    root_node_id: UUID
    active_node_id: UUID  # Currently selected
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
```

---

## 4. API Design

### 4.1 RESTful Endpoints

```
# Conversations
POST   /api/conversations              # Create new conversation
GET    /api/conversations              # List all conversations
GET    /api/conversations/{id}         # Get conversation details
DELETE /api/conversations/{id}         # Delete conversation
GET    /api/conversations/{id}/graph   # Get full graph structure

# Graph Navigation
POST   /api/conversations/{id}/select  # Select active node
POST   /api/conversations/{id}/branch  # Branch from active node

# Nodes
GET    /api/nodes/{id}                 # Get node details
DELETE /api/nodes/{id}                 # Delete node & descendants
GET    /api/nodes/{id}/ancestors       # Get ancestor path
GET    /api/nodes/{id}/children        # Get child nodes

# Streaming
WS     /api/stream/{conversation_id}   # WebSocket for LLM streaming
```

### 4.2 Example Request/Response

#### Create Conversation
```http
POST /api/conversations
Content-Type: application/json

{
  "title": "Architecture Discussion",
  "initial_context": "You are a helpful software architect."
}

Response:
{
  "conversation_id": "uuid",
  "root_node_id": "uuid",
  "active_node_id": "uuid"
}
```

#### Branch from Node
```http
POST /api/conversations/{id}/branch
Content-Type: application/json

{
  "query": "What about using microservices?",
  "model": "google/gemma-2-9b-it:free",
  "stream": true
}

Response (streaming via WebSocket):
{
  "type": "token",
  "content": "Micro"
}
{
  "type": "token",
  "content": "services "
}
{
  "type": "complete",
  "node_id": "new-uuid",
  "metadata": {
    "tokens": 245,
    "latency_ms": 1203
  }
}
```

---

## 5. Implementation Phases (Fast Track)

### Phase 1: Backend Core (Days 1-2)
**Goal:** Working in-memory API

**Tasks:**
1. FastAPI project setup
2. Implement in-memory data models
3. Create conversation CRUD endpoints
4. Implement graph navigation logic
5. Write basic tests

**Deliverable:** API that creates and navigates conversation graphs

### Phase 2: LLM Integration (Days 2-3)
**Goal:** Connect OpenRouter and stream responses

**Tasks:**
1. OpenRouter client with httpx
2. Streaming response handler
3. WebSocket endpoint for real-time streaming
4. Context building from ancestor path
5. Error handling and rate limiting

**Deliverable:** End-to-end query → response flow

### Phase 3: Beautiful Frontend (Days 3-5)
**Goal:** Gorgeous, interactive UI

**Tasks:**
1. React + Vite + TypeScript setup
2. shadcn/ui component installation
3. React Flow graph visualization
4. Custom node components with animations
5. Context viewer/editor panel
6. Responsive layout (desktop + mobile)

**Deliverable:** Beautiful working UI

### Phase 4: Polish & UX (Days 5-7)
**Goal:** Delightful user experience

**Tasks:**
1. Smooth transitions and animations
2. Loading states and skeletons
3. Error messages and retry logic
4. Keyboard shortcuts
5. Export/import conversations (JSON)
6. Dark mode toggle

**Deliverable:** Production-quality MVP

---

## 6. Project Structure (Simple)

```
converge/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app
│   │   ├── models.py               # Data models
│   │   ├── store.py                # In-memory storage
│   │   ├── api/
│   │   │   ├── conversations.py    # Conversation endpoints
│   │   │   ├── nodes.py            # Node endpoints
│   │   │   └── stream.py           # WebSocket streaming
│   │   └── services/
│   │       ├── llm.py              # OpenRouter client
│   │       └── graph.py            # Graph operations
│   ├── requirements.txt
│   └── .env                        # OPENROUTER_API_KEY
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Graph/
│   │   │   │   ├── GraphView.tsx   # Main graph canvas
│   │   │   │   ├── CustomNode.tsx  # Beautiful node component
│   │   │   │   └── CustomEdge.tsx  # Styled edges
│   │   │   ├── Panels/
│   │   │   │   ├── ContextPanel.tsx
│   │   │   │   ├── QueryPanel.tsx
│   │   │   │   └── ConversationList.tsx
│   │   │   └── ui/                 # shadcn components
│   │   ├── hooks/
│   │   │   ├── useConversation.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useGraph.ts
│   │   ├── lib/
│   │   │   └── api.ts              # API client
│   │   ├── types/
│   │   │   └── graph.ts
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── .env.example
└── README.md
```

---

## 7. Beautiful UI Design

### 7.1 Graph Visualization

**Node Design:**
- Rounded corners with subtle shadows
- Color-coded by depth or type
- Smooth hover effects
- Display snippet of response
- Badges for token count, model

**Edge Design:**
- Smooth curves (Bezier)
- Animated on creation
- Query text on hover
- Different styles for active path

**Layout:**
- Tree layout (top-to-bottom or left-to-right)
- Auto-layout with dagre
- Manual position override
- Mini-map for large graphs

### 7.2 Color Palette (Modern & Clean)

```css
/* Light Mode */
--background: #ffffff
--foreground: #0a0a0a
--primary: #3b82f6      /* Blue */
--secondary: #8b5cf6    /* Purple */
--accent: #06b6d4       /* Cyan */
--muted: #f1f5f9

/* Dark Mode */
--background: #0a0a0a
--foreground: #fafafa
--primary: #60a5fa
--secondary: #a78bfa
--accent: #22d3ee
--muted: #1e293b
```

### 7.3 Key Features for Beauty

1. **Smooth Animations**
   - Framer Motion for transitions
   - Staggered fade-ins
   - Smooth graph layout changes

2. **Typography**
   - Inter font family
   - Proper hierarchy
   - Syntax highlighting (Shiki)

3. **Feedback**
   - Toast notifications (sonner)
   - Loading skeletons
   - Progress indicators

4. **Accessibility**
   - Keyboard navigation
   - ARIA labels
   - Focus indicators
   - Screen reader support

---

## 8. OpenRouter Integration (With Automatic Fallback)

### 8.1 Production-Ready Implementation

**Critical:** This implementation includes automatic model fallback - essential for reliability with free models.

```python
# backend/app/services/llm.py

import httpx
import json
import os
from typing import AsyncGenerator, Optional
from pathlib import Path
from dotenv import load_dotenv

# CRITICAL: Load .env from project root
env_path = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class OpenRouterClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        self.base_url = "https://openrouter.ai/api/v1"

        # Free models to try in order (CRITICAL for reliability)
        self.free_models = [
            "meta-llama/llama-3.3-70b-instruct:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "amazon/nova-2-lite-v1:free",
            "openai/gpt-oss-20b:free",
            "google/gemma-3-27b-it:free",
            "mistralai/mistral-7b-instruct:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "alibaba/tongyi-deepresearch-30b-a3b:free",
            "moonshotai/kimi-k2:free"
        ]

    async def stream_response(
        self,
        context: str,
        query: str,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response with automatic model fallback"""

        # If specific model provided, try only that one
        # Otherwise try all free models in sequence
        models_to_try = [model] if model else self.free_models

        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": query}
        ]

        last_error = None

        for model_name in models_to_try:
            print(f"🎯 Trying model: {model_name}")

            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "HTTP-Referer": "https://converge.local",
                            "X-Title": "ConVerge"
                        },
                        json={
                            "model": model_name,
                            "messages": messages,
                            "stream": True
                        }
                    ) as response:
                        if response.status_code != 200:
                            error_body = await response.aread()
                            print(f"❌ Model {model_name} failed: {error_body.decode()}")
                            last_error = f"HTTP {response.status_code}"
                            continue  # Try next model

                        print(f"✅ Model {model_name} accepted! Starting stream...")

                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()

                                if data_str == "[DONE]":
                                    return

                                try:
                                    data = json.loads(data_str)
                                    if content := data.get("choices", [{}])[0].get("delta", {}).get("content"):
                                        yield content
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    continue

                        return  # Success

            except Exception as e:
                print(f"❌ Error with {model_name}: {e}")
                last_error = str(e)
                continue  # Try next model

        # If all models failed
        raise Exception(f"All models failed. Last error: {last_error}")

# Lazy initialization (CRITICAL to avoid loading before .env)
_llm_client = None

def get_llm_client() -> OpenRouterClient:
    """Get or create the global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenRouterClient()
    return _llm_client
```

---

## 9. Quick Start (Tested & Working)

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenRouter API key (get free at https://openrouter.ai)

### Setup & Run

```bash
# 1. Create .env file in PROJECT ROOT (not in backend/)
cd conVerge  # Your project root
cat > .env << 'EOF'
OPENROUTER_API_KEY=sk-or-v1-your-key-here
DEFAULT_MODEL=meta-llama/llama-3.2-3b-instruct:free
CORS_ORIGINS=http://localhost:5173
EOF

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn httpx pydantic python-dotenv websockets

# CRITICAL: Ensure .env is in parent directory
# The backend loads it from: Path(__file__).parent.parent.parent / '.env'

# Run backend
uvicorn app.main:app --reload --port 8000

# 3. Frontend setup (new terminal)
cd frontend

# CRITICAL: Use exact versions to avoid compatibility issues
npm install react@^19.2.0 react-dom@^19.2.0
npm install -D tailwindcss@3.4.1 postcss autoprefixer
npm install @tanstack/react-query@^5.90.14
npm install reactflow@^11.11.4  # v11, not v10
npm install zustand@^5.0.9
npm install dagre @types/dagre

# Initialize Tailwind (v3, not v4!)
npx tailwindcss init -p

# Run frontend
npm run dev
```

**That's it!** Open http://localhost:5173

### Verification Steps

1. **Backend:** Visit http://localhost:8000/docs - Should see FastAPI docs
2. **Frontend:** Should see "🌳 ConVerge" header with "+ New Conversation" button
3. **Create conversation** - Click button, enter title and context
4. **Submit query** - Type query, press **Enter** to submit
5. **Watch console** - Backend terminal shows model attempts and streaming progress

---

## 10. Critical Implementation Notes (Lessons Learned)

### 10.1 Environment Variable Loading

**Problem:** Backend couldn't find OPENROUTER_API_KEY even though it existed in .env

**Solution:** Load .env from project root, not backend subdirectory

```python
# backend/app/main.py
from pathlib import Path
from dotenv import load_dotenv

# Load from parent directory (project root)
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
```

**Also in:** `backend/app/services/llm.py` (needs same fix)

### 10.2 Lazy Initialization for LLM Client

**Problem:** LLM client instantiated at module import time, before .env loaded

**Solution:** Use lazy initialization with getter function

```python
# backend/app/services/llm.py
_llm_client = None

def get_llm_client() -> OpenRouterClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenRouterClient()
    return _llm_client

# backend/app/api/conversations.py
from ..services.llm import get_llm_client

# Use get_llm_client() NOT llm_client
async for token in get_llm_client().stream_response(...):
```

### 10.3 React Flow v11 Type Issues

**Problem:** `Node`, `Edge`, and `NodeProps` don't exist in React Flow v11 exports

**Solution:** Define custom types instead of importing

```typescript
// frontend/src/components/GraphView.tsx
import ReactFlow, {
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  ConnectionLineType,
  MarkerType,
} from 'reactflow';

// DON'T import Node, Edge - they don't exist!
// Define custom types instead:
type FlowNode = {
  id: string;
  type?: string;
  data: any;
  position: { x: number; y: number };
};

type FlowEdge = {
  id: string;
  source: string;
  target: string;
  type?: string;
  animated?: boolean;
  markerEnd?: any;
  label?: string;
};
```

```typescript
// frontend/src/components/CustomNode.tsx
import { Handle, Position } from 'reactflow';
// DON'T import NodeProps!

interface CustomNodeProps {
  data: NodeData;
  selected?: boolean;
}

export const CustomNode = memo(({ data, selected }: CustomNodeProps) => {
  // ...
});
```

### 10.4 Tailwind CSS Version

**Problem:** Tailwind v4 has breaking changes and incompatible PostCSS plugin syntax

**Solution:** Use stable Tailwind CSS v3.4.1

```bash
# DON'T install @tailwindcss/postcss (that's for v4)
npm install -D tailwindcss@3.4.1 postcss autoprefixer
```

```js
// postcss.config.js - Simple v3 syntax
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### 10.5 UUID JSON Serialization

**Problem:** WebSocket `StreamComplete` message failed: "UUID is not JSON serializable"

**Solution:** Convert UUID to string before sending

```python
# backend/app/schemas.py
class StreamComplete(BaseModel):
    type: str = "complete"
    node_id: str  # str, not UUID!
    metadata: dict

# backend/app/api/conversations.py
await websocket.send_json(StreamComplete(
    node_id=str(new_node.id),  # Convert UUID to string
    metadata={...}
).model_dump())
```

### 10.6 Enter Key to Submit

**Problem:** Users expected Enter to submit, but it created new line

**Solution:** Add keyboard handler

```typescript
// frontend/src/components/QueryPanel.tsx
const handleKeyDown = useCallback(
  (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (query.trim() && !isStreaming) {
        onSubmit(query.trim());
        setQuery('');
      }
    }
  },
  [query, onSubmit, isStreaming]
);

<textarea onKeyDown={handleKeyDown} ... />
```

### 10.7 OpenRouter Model Availability

**Problem:** Free models return 404 "Not Found" unpredictably

**Solution:** Automatic fallback through model list (see Section 8.1)

**Key Points:**
- NEVER assume a free model is available
- ALWAYS implement model iteration
- Log which model succeeded for debugging
- Pass `model=None` to try all free models

### 10.8 WebSocket Error Handling

**Critical additions for debugging:**

```python
# backend/app/api/conversations.py
@router.websocket("/{conversation_id}/stream")
async def websocket_stream(websocket: WebSocket, conversation_id: UUID):
    print(f"🔌 WebSocket connection attempt: {conversation_id}")
    await websocket.accept()
    print(f"✅ WebSocket accepted")

    try:
        # ... your code ...
        print(f"📥 Received data: {data}")
        print(f"🤖 Starting LLM streaming...")
        # ... streaming ...
        print(f"✅ Streaming complete")

    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected by client")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
```

### 10.9 Complete Component List Required

**Problem:** App showed white screen because components weren't created

**All required files:**

```
frontend/src/
├── types/
│   └── graph.ts             # MUST create - type definitions
├── lib/
│   └── api.ts               # MUST create - API client
├── hooks/
│   ├── useConversation.ts   # MUST create - React Query hooks
│   └── useWebSocket.ts      # MUST create - WebSocket streaming
├── components/
│   ├── CustomNode.tsx       # MUST create - Graph node component
│   ├── GraphView.tsx        # MUST create - React Flow canvas
│   ├── ContextPanel.tsx     # MUST create - Node details panel
│   └── QueryPanel.tsx       # MUST create - Query input
├── App.tsx                  # Main app (already exists from Vite)
├── main.tsx                 # Entry point (already exists)
└── index.css                # Tailwind imports
```

**Don't skip any of these!** Each component is essential.

---

## 11. Key Design Decisions

### 10.1 Why In-Memory Storage?

**Decision:** Use Python dictionaries instead of database

**Rationale:**
- Zero setup time (no Docker, no migrations)
- Perfect for MVP and demos
- Blazing fast operations
- Simple to understand and debug
- Data resets are acceptable for this use case
- Can add persistence later if needed (pickle, JSON export)

### 10.2 Why Keep React Flow?

**Decision:** Still use React Flow despite simplified backend

**Rationale:**
- Best-in-class graph visualization
- Beautiful out of the box
- Makes the app feel professional
- Worth the complexity on frontend

### 10.3 Context Storage Strategy

**Decision:** Store full context in each node

**Rationale:**
- Transparent - users see exactly what LLM received
- Enables context editing before branching
- Simple to implement
- Memory usage acceptable for session-based storage

---

## 12. Success Criteria (Tested & Working)

### MVP Must-Haves

- ✅ Create conversation with initial context
- ✅ Submit query with Enter key
- ✅ Automatic LLM model fallback (tries up to 9 free models)
- ✅ Real-time WebSocket streaming responses
- ✅ Click any node to make it active
- ✅ Branch from any node
- ✅ Beautiful graph visualization with React Flow
- ✅ Auto-layout with dagre algorithm
- ✅ View full context and response per node
- ✅ Multiple conversations
- ✅ Delete nodes (and their descendants)
- ✅ Session-based in-memory storage
- ✅ Comprehensive error logging
- ✅ CORS configured for localhost development

### Beauty & UX Standards

- ✅ Smooth graph animations with React Flow
- ✅ Tailwind CSS v3 utility styling
- ✅ Dark mode support (dark:bg-gray-900)
- ✅ Professional typography (system-ui font stack)
- ✅ Keyboard shortcuts (Enter to submit)
- ✅ Real-time streaming with animated cursor
- ✅ Color-coded nodes (purple for root, blue for branches)
- ✅ Hover effects on nodes and buttons
- ✅ Responsive 3-column layout (Context | Graph | Query)

---

## 12. Future Enhancements (Post-MVP)

When in-memory isn't enough:

1. **Add Persistence**
   - Local storage (browser)
   - JSON export/import
   - SQLite file (simple upgrade)
   - Eventually PostgreSQL

2. **Advanced Features**
   - Context summarization
   - Search within conversation
   - Node annotations
   - Collaborative editing
   - Version history

3. **Performance**
   - Virtual scrolling for large graphs
   - Lazy loading subtrees
   - Context compression

---

## 13. Troubleshooting Guide

### White Screen on Frontend

**Symptoms:** Browser shows blank page, no errors in terminal

**Check:**
1. Browser console (F12) for JavaScript errors
2. All components created? (See Section 10.9)
3. React Flow imports correct? (See Section 10.3)
4. Tailwind CSS version? (Should be v3.4.1, not v4)

### "OPENROUTER_API_KEY not found"

**Symptoms:** Backend crashes on startup or first request

**Fix:**
1. .env file in **project root**, not backend/
2. Load .env in both main.py and llm.py
3. Use lazy initialization (See Section 10.2)

### "404 Not Found" from OpenRouter

**Symptoms:** Query hangs, then error alert shows "404 Not Found"

**Expected!** Free models are unreliable. Check:
1. Automatic fallback implemented? (See Section 8.1)
2. Backend logs show "🎯 Trying model: ..." for each attempt?
3. At least one model should succeed from the list

### WebSocket Connection Fails

**Symptoms:** Query submitted but nothing happens

**Check:**
1. Backend logs show "🔌 WebSocket connection attempt"?
2. CORS headers configured?
3. Frontend using correct WebSocket URL: `ws://localhost:8000/api/conversations/{id}/stream`

### UUID Serialization Error

**Symptoms:** "Object of type UUID is not JSON serializable"

**Fix:**
```python
# Convert UUIDs to strings before JSON serialization
node_id=str(new_node.id)  # NOT node_id=new_node.id
```

### React Flow Types Not Found

**Symptoms:** "The requested module '/node_modules/.vite/deps/reactflow.js' does not provide an export named 'Node'"

**Fix:** Don't import `Node`, `Edge`, or `NodeProps` - they don't exist in v11. Use custom types (See Section 10.3)

---

## 14. Timeline

**Total: 5-7 days for beautiful MVP**

- Days 1-2: Backend core + LLM integration
- Days 3-5: Frontend with React Flow
- Days 5-7: Polish, animations, UX refinement

**First demo-ready version: Day 5**

---

## 15. Verified Working Implementation

### What's Built & Tested ✅

1. ✅ **Backend with in-memory storage** - Python dicts, zero setup
2. ✅ **FastAPI with WebSocket streaming** - Real-time LLM responses
3. ✅ **OpenRouter integration with fallback** - Tries 9 free models automatically
4. ✅ **React + TypeScript frontend** - Beautiful graph UI
5. ✅ **React Flow v11 graph visualization** - Interactive node canvas
6. ✅ **Tailwind CSS v3 styling** - Clean, modern design
7. ✅ **TanStack Query state management** - Real-time updates
8. ✅ **Dagre auto-layout** - Automatic graph positioning
9. ✅ **Comprehensive error handling** - Detailed logging
10. ✅ **Environment variable management** - Proper .env loading

### Implementation Decisions Made

1. **Graph Layout:** Top-to-bottom tree (vertical flow)
2. **Initial Context:** User-provided via prompt
3. **Model Selection:** Automatic fallback (no picker needed)
4. **Keyboard UX:** Enter to submit, Shift+Enter for new line
5. **Storage:** Session-based (data resets on restart - by design)
6. **Styling:** Dark mode ready, responsive 3-column layout

### Next Enhancements (Post-MVP)

1. **Persistence:** JSON export/import for conversations
2. **Model picker:** UI to select specific model
3. **Context editing:** Edit context before branching
4. **Search:** Find nodes by query or response text
5. **Analytics:** Token usage tracking, cost estimation
6. **Multi-user:** Add authentication and user management

---

## Appendix A: Exact Working `.env`

Place in **project root** (not in backend/):

```bash
# OpenRouter API Key (get free at https://openrouter.ai)
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here

# Optional: Default model (fallback will try all free models anyway)
DEFAULT_MODEL=meta-llama/llama-3.2-3b-instruct:free

# CORS (for local development)
CORS_ORIGINS=http://localhost:5173
```

---

## Appendix B: Working `package.json` Dependencies

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.90.14",
    "@types/dagre": "^0.7.53",
    "dagre": "^0.8.5",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "reactflow": "^11.11.4",
    "zustand": "^5.0.9"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^5.1.1",
    "autoprefixer": "^10.4.23",
    "postcss": "^8.5.6",
    "tailwindcss": "^3.4.1",
    "typescript": "~5.9.3",
    "vite": "^7.2.4"
  }
}
```

**Critical:** Tailwind must be `3.4.1`, not `4.x`

---

## Appendix C: Backend Requirements

```txt
fastapi==0.115.12
uvicorn==0.34.11
httpx==0.28.1
pydantic==2.12.11
python-dotenv==1.0.1
websockets==14.2
```

Install with: `pip install -r requirements.txt`

---

## Appendix D: References & Resources

- **ConVerge Paper:** `conVerge.tex` (theoretical foundation)
- **OpenRouter API:** https://openrouter.ai/docs
- **React Flow v11:** https://reactflow.dev/
- **FastAPI:** https://fastapi.tiangolo.com/
- **Tailwind CSS v3:** https://v3.tailwindcss.com/
- **TanStack Query:** https://tanstack.com/query/latest
- **Dagre Layout:** https://github.com/dagrejs/dagre

---

## Appendix E: Testing Checklist

Before considering MVP complete, test:

- [ ] Create new conversation
- [ ] Submit query with Enter key
- [ ] See streaming response appear token-by-token
- [ ] New node appears in graph
- [ ] Click different nodes to switch active
- [ ] Submit query from non-root node (branching)
- [ ] Delete conversation
- [ ] Create multiple conversations
- [ ] Switch between conversations
- [ ] Check backend logs show model attempts
- [ ] Verify at least one free model works
- [ ] Test in different browsers (Chrome, Firefox, Safari)
- [ ] Check dark mode works
- [ ] Test responsive layout

---

**Document Version:** 3.0 (Battle-Tested)
**Updated:** 2025-12-29
**Status:** ✅ Fully Implemented & Working
**Tested On:** macOS, Python 3.11, Node.js 18
**Philosophy:** Simple, Beautiful, **Actually Works**
