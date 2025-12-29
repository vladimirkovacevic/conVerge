# 🌳 ConVerge - Graph-Based Conversation Management

**User-controlled conversational context through interactive graph visualization**

ConVerge enables non-linear navigation of AI conversations, allowing you to branch conversations, explore alternative reasoning paths, and maintain full transparency of conversational context.

---

## ✨ Features

- 🌳 **Graph Visualization** - Interactive conversation tree with React Flow
- 🔀 **Non-linear Navigation** - Branch from any node, explore multiple paths
- 💬 **Real-time Streaming** - Watch LLM responses appear token-by-token
- 👁️ **Context Transparency** - See exact context used for each response
- 🎨 **Beautiful UI** - Modern design with dark mode support
- ⚡ **Zero Setup** - In-memory storage, no database required
- 🆓 **Free to Use** - Uses free OpenRouter models by default

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.11+
- Node.js 18+
- OpenRouter API key (free at [openrouter.ai](https://openrouter.ai))

### **1. Clone & Setup**

```bash
cd conVerge
```

### **2. Configure Environment**

Create `.env` file in the root directory:

```bash
OPENROUTER_API_KEY=your-key-here
```

Get your free API key from [openrouter.ai/keys](https://openrouter.ai/keys)

### **3. Start Backend**

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```

Backend running at **http://localhost:8000**
- API docs: **http://localhost:8000/docs**

### **4. Start Frontend** (new terminal)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend running at **http://localhost:5173**

### **5. Open in Browser**

Navigate to **http://localhost:5173** and start conversing! 🎉

---

## 📖 How to Use

1. **Create a Conversation**
   - Click "+ New Conversation"
   - Enter a title and initial system context
   - Your first conversation appears!

2. **Ask Questions**
   - Type your query in the right panel
   - Press `Cmd/Ctrl + Enter` or click "Send Query"
   - Watch the response stream in real-time

3. **Navigate the Graph**
   - Click any node to select it
   - Ask another question to branch from that node
   - Explore different conversation paths non-linearly

4. **View Details**
   - **Left Panel**: Node details, full context, response
   - **Center Panel**: Interactive graph visualization
   - **Right Panel**: Query input and streaming responses

---

## 🏗️ Architecture

```
┌─────────────────────┐
│   Frontend UI       │ ← React + React Flow
└──────────┬──────────┘
           │ REST API + WebSocket
┌──────────▼──────────┐
│   Backend API       │ ← FastAPI (Python)
│   ┌─────────────┐   │
│   │ In-Memory   │   │ ← Python dicts (session storage)
│   │ Storage     │   │
│   └─────────────┘   │
│   ┌─────────────┐   │
│   │ LLM Client  │   │ ← OpenRouter API
│   └─────────────┘   │
└─────────────────────┘
```

### **Tech Stack**

**Frontend:**
- React 18 + TypeScript
- React Flow (graph visualization)
- TanStack Query (state management)
- Tailwind CSS (styling)
- Zustand (global state)

**Backend:**
- FastAPI (async Python framework)
- Pydantic v2 (validation)
- httpx (async HTTP client)
- WebSocket (streaming)

---

## 📁 Project Structure

```
conVerge/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── conversations.py    # Conversation endpoints
│   │   │   └── nodes.py            # Node endpoints
│   │   ├── services/
│   │   │   └── llm.py              # OpenRouter client
│   │   ├── main.py                 # FastAPI app
│   │   ├── models.py               # Data models
│   │   ├── store.py                # In-memory storage
│   │   └── schemas.py              # API schemas
│   ├── requirements.txt
│   └── venv/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── GraphView.tsx       # Graph visualization
│   │   │   ├── CustomNode.tsx      # Node component
│   │   │   ├── ContextPanel.tsx    # Context viewer
│   │   │   └── QueryPanel.tsx      # Query input
│   │   ├── hooks/
│   │   │   ├── useConversation.ts  # API hooks
│   │   │   └── useWebSocket.ts     # Streaming hook
│   │   ├── lib/
│   │   │   └── api.ts              # API client
│   │   ├── types/
│   │   │   └── graph.ts            # TypeScript types
│   │   └── App.tsx                 # Main app
│   ├── package.json
│   └── node_modules/
│
├── .env                            # Environment variables
├── IMPLEMENTATION_PLAN.md          # Technical implementation plan
└── README.md                       # This file
```

---

## 🔌 API Endpoints

### **Conversations**

```
POST   /api/conversations              # Create conversation
GET    /api/conversations              # List all conversations
GET    /api/conversations/{id}         # Get conversation details
DELETE /api/conversations/{id}         # Delete conversation
GET    /api/conversations/{id}/graph   # Get full graph structure
POST   /api/conversations/{id}/select  # Select active node
WS     /api/conversations/{id}/stream  # Stream LLM responses
```

### **Nodes**

```
GET    /api/nodes/{id}                 # Get node details
DELETE /api/nodes/{id}                 # Delete node & descendants
GET    /api/nodes/{id}/ancestors       # Get path from root
GET    /api/nodes/{id}/children        # Get child nodes
```

Explore the full API at **http://localhost:8000/docs**

---

## ⚙️ Configuration

### **Backend (.env)**

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-...

# Optional
DEFAULT_MODEL=google/gemma-2-9b-it:free
CORS_ORIGINS=http://localhost:5173
```

### **Frontend (.env)**

```bash
VITE_API_URL=http://localhost:8000
```

---

## 💾 Data Storage

**In-Memory Storage**
- All data stored in Python dictionaries
- Fast access, zero setup
- Data resets when backend restarts
- Perfect for demos and development

**Future Options:**
- Local storage (browser)
- JSON export/import
- SQLite database
- PostgreSQL (full persistence)

---

## 🆓 Free LLM Models

ConVerge uses free OpenRouter models by default:

- `google/gemma-2-9b-it:free` - Fast, capable
- `meta-llama/llama-3.1-8b-instruct:free` - Large context (128K)
- `qwen/qwen-2-7b-instruct:free` - Efficient

Upgrade to paid models for better quality and higher rate limits.

---

## 🛑 Troubleshooting

**Backend won't start?**
```bash
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

**Frontend won't start?**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**WebSocket connection fails?**
- Check backend is running on port 8000
- Verify browser console for errors
- Ensure `.env` has correct `VITE_API_URL`

**API key issues?**
- Get free key at [openrouter.ai/keys](https://openrouter.ai/keys)
- Add to `.env` as `OPENROUTER_API_KEY=...`
- Restart backend server

---

## 📚 References

- **Paper**: `conVerge.tex` - Formal specification
- **Plan**: `IMPLEMENTATION_PLAN.md` - Technical implementation
- **OpenRouter**: https://openrouter.ai/docs
- **React Flow**: https://reactflow.dev
- **FastAPI**: https://fastapi.tiangolo.com

---

## 🎯 What's Next?

**Planned Features:**
- [ ] Export conversations (JSON, Markdown)
- [ ] Import conversations
- [ ] Search within conversations
- [ ] Browser local storage persistence
- [ ] Multiple model selection
- [ ] Node annotations and tags
- [ ] Keyboard shortcuts
- [ ] Mobile responsive design

---

## 📝 License

MIT

---

## 🙏 Contributing

Contributions welcome! Feel free to open issues or submit PRs.

---

**Built with ❤️ using React, FastAPI, and React Flow**
