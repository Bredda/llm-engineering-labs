# \_template — LangGraph Chatbot

Template de base pour les démos `demo-apps`. Chatbot multi-turn avec streaming SSE, historique SQLite, et un seul nœud LangGraph.

## Stack

| Couche      | Choix                     | Pourquoi                                                  |
| ----------- | ------------------------- | --------------------------------------------------------- |
| Frontend    | Vite + React + TypeScript | Démarrage instantané, zéro config                         |
| Backend     | FastAPI + Python          | Standard de l'écosystème LLM                              |
| Streaming   | Server-Sent Events (SSE)  | Plus simple qu'un WebSocket pour du texte unidirectionnel |
| Persistance | SQLite via `SqliteSaver`  | Zéro infrastructure, géré par LangGraph                   |

## Architecture

```
Frontend (Vite :5173)          Backend (FastAPI :8000)
        │                               │
        │  POST /chat/stream            │
        │──────────────────────────────►│
        │                               │  SqliteSaver
        │  SSE: { token: "..." }        │  (checkpoints.db)
        │◄──────────────────────────────│       │
        │  SSE: { done: true }          │  LangGraph ─── chat_node ─── LLM
        │                               │
        │  GET /chat/{thread_id}/history│
        │──────────────────────────────►│
        │  { messages: [...] }          │
        │◄──────────────────────────────│
```

## Pourquoi LangGraph avec un seul nœud ?

Un graph LangGraph avec un seul nœud est **fonctionnellement équivalent à un appel LLM direct**, mais il te donne :

- **Le checkpointer gratuit** — `SqliteSaver` gère l'historique par `thread_id` sans code supplémentaire
- **L'extensibilité** — ajouter un nœud RAG, un nœud d'outils, ou une boucle de réflexion = ajouter des nœuds et des arêtes, sans toucher à l'API ni au frontend
- **La traçabilité** — `astream_events` expose chaque événement du graph, utile pour le debug et les démos

```
START ──► chat_node ──► END
               │
               └── llm.invoke(state["messages"])
```

Pour cette démo, le graph ressemble à ça :

```python
graph = (
    StateGraph(State)
    .add_node("chat", chat_node)   # ← le seul nœud
    .add_edge(START, "chat")
    .add_edge("chat", END)
    .compile(checkpointer=memory)  # ← SqliteSaver branché ici
)
```

## Setup

### Prérequis

- Python 3.12+ avec [`uv`](https://docs.astral.sh/uv/) installé
- Node.js 20+
- Une clé OpenAI

### Installation

```bash
# 1. Cloner et se placer dans le dossier
cd demo-apps/_template

# 2. Installer tout d'un coup
make install

# 3. Configurer la clé API
cp backend/.env.example backend/.env
# → éditer backend/.env et renseigner OPENAI_API_KEY
```

### Lancement

```bash
make dev
# Lance backend (:8000) et frontend (:5173) en parallèle
```

Ouvrir http://localhost:5173

### Nettoyage de l'historique

```bash
make clean   # supprime checkpoints.db
```

## Persistance

La conversation est identifiée par un `thread_id` (UUID) stocké dans le `localStorage` du navigateur. Ce même ID est utilisé comme clé dans le checkpoint SQLite côté backend.

```
localStorage["thread_id"] = "f47ac10b-..."
                                  │
                                  ▼
              checkpoints.db  ←  SqliteSaver
              (backend/)
```

Recharger la page → le frontend envoie le `thread_id` existant → le backend restaure l'historique depuis SQLite. Cliquer "New chat" → nouveau UUID → nouvelle conversation.

## Packaging Docker

```bash
docker build -t chatbot-template .
docker run -e OPENAI_API_KEY=sk-... -p 8000:8000 chatbot-template
```

L'image embarque le frontend buildé servi en statique par FastAPI.  
Pour activer le serving statique, ajouter dans `main.py` :

```python
from fastapi.staticfiles import StaticFiles
import os

if os.getenv("SERVE_STATIC") == "true":
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

## Étendre ce template

Pour créer une nouvelle démo depuis ce template :

```bash
cp -r demo-apps/_template demo-apps/ma-nouvelle-demo
```

Points d'extension typiques :

- **Ajouter un nœud RAG** → nouveau nœud avant `chat_node`, edge `START → retrieval → chat → END`
- **Ajouter des outils** → `llm.bind_tools(...)` dans `chat_node`, nœud conditionnel `ToolNode`
- **Changer le modèle** → remplacer `ChatOpenAI` par `ChatAnthropic`, `ChatMistralAI`, etc.
