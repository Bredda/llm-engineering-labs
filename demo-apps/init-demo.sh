#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# new-demo.sh — Bootstrap a new demo app from _template
#
# Usage:
#   ./new-demo.sh
#   → prompts for a demo name and creates demo-apps/<name>/
# ──────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Input ─────────────────────────────────────────────────────────────────────

read -rp "Demo name (lowercase, hyphen-separated, e.g. graph-rag): " NAME

if [[ ! "$NAME" =~ ^[a-z0-9-]+$ ]]; then
  echo "Error: demo name must be lowercase letters, digits, and hyphens only"
  exit 1
fi

# ── Paths ─────────────────────────────────────────────────────────────────────

DEMO_APPS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$DEMO_APPS_DIR/_template"
TARGET_DIR="$DEMO_APPS_DIR/$NAME"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "Error: template not found at $TEMPLATE_DIR"
  exit 1
fi

if [[ -d "$TARGET_DIR" ]]; then
  echo "Error: $TARGET_DIR already exists"
  exit 1
fi

# ── Derived names ─────────────────────────────────────────────────────────────

# graph-rag → GraphRag  (PascalCase — FastAPI title, UI header)
PASCAL_NAME=$(echo "$NAME" | sed -E 's/(^|-)([a-z])/\U\2/g')

# graph-rag → graph_rag  (snake_case — Python module name)
SNAKE_NAME="${NAME//-/_}"

# ── Copy (exclude runtime/local artifacts) ────────────────────────────────────

echo "→ Copying template to $TARGET_DIR"
rsync -a \
  --exclude='.venv' \
  --exclude='.env' \
  --exclude='node_modules' \
  --exclude='dist' \
  --exclude='*.sqlite' \
  "$TEMPLATE_DIR/" "$TARGET_DIR/"

# ── Rename Python module folder: template_api → <snake_name>_api ──────────────

echo "→ Renaming Python module"
mv "$TARGET_DIR/api/template_api" "$TARGET_DIR/api/${SNAKE_NAME}_api"

# ── sed helper (BSD vs GNU) ───────────────────────────────────────────────────

if sed --version &>/dev/null 2>&1; then
  SED_I="sed -i"      # GNU (Linux)
else
  SED_I="sed -i ''"   # BSD (macOS)
fi

# ── Substitutions in source files ─────────────────────────────────────────────
#
# Template literals to replace:
#   template_api          → <snake_name>_api   (Python module, pyproject.toml)
#   template-api          → <snake_name>-api   (pyproject.toml name field)
#   template-ui           → <name>-ui          (package.json name field)
#   LangGraph Chatbot     → <PascalName> Demo  (FastAPI title, UI header)
#   chatbot-template      → <name>             (residual refs)
#   chatbot_template      → <snake_name>        (residual refs)

echo "→ Replacing template references"

find "$TARGET_DIR" -type f \( \
  -name "*.py"   -o \
  -name "*.ts"   -o \
  -name "*.tsx"  -o \
  -name "*.json" -o \
  -name "*.toml" -o \
  -name "*.md"   -o \
  -name "*.html" -o \
  -name "Dockerfile" -o \
  -name "Makefile" \
\) | while read -r file; do
  $SED_I \
    -e "s/template_api/${SNAKE_NAME}_api/g" \
    -e "s/template-api/${SNAKE_NAME}-api/g" \
    -e "s/template-ui/${NAME}-ui/g" \
    -e "s/LangGraph Chatbot Template/${PASCAL_NAME} Demo/g" \
    -e "s/LangGraph Chatbot/${PASCAL_NAME} Demo/g" \
    -e "s/chatbot-template/${NAME}/g" \
    -e "s/chatbot_template/${SNAKE_NAME}/g" \
    "$file"
done

# ── descriptions in pyproject.toml and package.json ───────────────────────────

$SED_I \
  -e "s/^description = .*/description = \"API for ${NAME}\"/" \
  "$TARGET_DIR/api/pyproject.toml"

$SED_I \
  -e "s/\"description\": .*/\"description\": \"UI for ${NAME}\",/" \
  "$TARGET_DIR/ui/package.json"

# ── Rename checkpoint reference in main.py ────────────────────────────────────

$SED_I \
  -e "s/checkpoints\.sqlite/${SNAKE_NAME}_checkpoints.sqlite/g" \
  "$TARGET_DIR/api/${SNAKE_NAME}_api/main.py"

# ── Generate README ───────────────────────────────────────────────────────────

cat > "$TARGET_DIR/README.md" << README
# ${NAME}

Initialisé depuis [_template](../_template).

## Setup

\`\`\`bash
cp api/.env.example api/.env   # ajouter OPENAI_API_KEY
make install
\`\`\`

## Dev

\`\`\`bash
make dev        # api :8000 + ui :5173
make clean      # vider le checkpoint SQLite
\`\`\`

## Build

\`\`\`bash
make build      # image Docker taguée '${NAME}'
docker run -e OPENAI_API_KEY=sk-... -p 8000:8000 ${NAME}
\`\`\`
README

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
echo "✓ Demo '${NAME}' created at ${TARGET_DIR}"
echo ""
echo "Next steps:"
echo "  cd ${NAME}"
echo "  cp api/.env.example api/.env  # add your OPENAI_API_KEY"
echo "  make install"
echo "  make dev"