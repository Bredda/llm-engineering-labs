# code-graph

Initialisé depuis [_template](../_template).

## Setup

```bash
cp api/.env.example api/.env   # ajouter OPENAI_API_KEY
make install
```

## Dev

```bash
make dev        # api :8000 + ui :5173
make clean      # vider le checkpoint SQLite
```

## Build

```bash
make build      # image Docker taguée 'code-graph'
docker run -e OPENAI_API_KEY=sk-... -p 8000:8000 code-graph
```
