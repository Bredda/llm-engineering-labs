# demo-apps

Démos standalone avec vraie UI pour les talks **llm-engineering-labs**.

Chaque démo est self-contained : un `docker-compose up` pour les services externes,
un `uvicorn` pour l'app, et c'est prêt.

## Démos disponibles

| Dossier                | Thème                            | Services |
| ---------------------- | -------------------------------- | -------- |
| `_template`            | Squelette de base                | —        |
| `generative-ui-stream` | Streaming SSE + rendu temps réel | —        |
| `graph-rag-codebase`   | Graph RAG d'une codebase Python  | Neo4j    |

## Prérequis communs

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker + Docker Compose (pour les démos avec services externes)
- Une clé OpenAI dans le `.env` de chaque démo

## Démarrage rapide

```bash
cd <nom-de-la-demo>
cp .env.example .env          # renseigner OPENAI_API_KEY etc.
docker-compose up -d          # services externes (si nécessaire)
uv sync
uv run uvicorn main:app --reload --port 8000
```

→ Ouvrir http://localhost:8000

## Créer une nouvelle démo

```bash
cp -r _template ma-nouvelle-demo
```

Voir `_template/README.md` pour la checklist complète.

## Stack

- **Backend** : FastAPI + Uvicorn
- **Frontend** : Vanilla JS + HTML (zéro build step)
- **LLM** : OpenAI API via `langchain-openai`
- **Deps** : `uv` + `pyproject.toml`
- **Services** : Docker Compose (Neo4j, Chroma, Redis selon la démo)
