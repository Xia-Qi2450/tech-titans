#!/bin/bash

set -e

# Always run from the project root
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Paths
PYTHON="$ROOT/.venv/bin/python"
API_DIR="$ROOT/tech-titans-api"
SHEET="$ROOT/tech-titans-parse/Tech Titans Podcast Master Sheet.xlsx"

echo "╭──────────────────────────────────────────────╮"
echo "│        Tech Titans Development Server        │"
echo "╰──────────────────────────────────────────────╯"
echo

# Check virtual environment
if [ ! -x "$PYTHON" ]; then
    echo "× Virtual environment not found:"
    echo "   $PYTHON"
    echo
    echo "Create it with:"
    echo "   python -m venv .venv"
    exit 1
fi

# Check spreadsheet
if [ ! -f "$SHEET" ]; then
    echo "× Spreadsheet not found:"
    echo "   $SHEET"
    exit 1
fi

echo "📊 Parsing podcast spreadsheet..."
cd "$API_DIR"

"$PYTHON" podcast_sheet_parser.py "$SHEET" -v

echo
echo "🌱 Seeding database..."

"$PYTHON" seed_from_podcast_sheet.py \
    --from-json "$API_DIR/output/Tech Titans Podcast Master Sheet.json"

echo
echo "🚀 Starting API..."

cd "$ROOT"

"$PYTHON" "$API_DIR/app.py" &
API_PID=$!

echo "   API PID: $API_PID"
echo "   API: http://127.0.0.1:5000"

echo
echo "🌐 Starting website..."

cd "$ROOT/tech-titans-site"

"$PYTHON" -m http.server 8080 &
SITE_PID=$!

echo "   Site PID: $SITE_PID"
echo "   Site: http://localhost:8080"
echo

# Clean up both servers when script exits
cleanup() {
    echo
    echo "🛑 Shutting down development servers..."

    kill "$API_PID" 2>/dev/null || true
    kill "$SITE_PID" 2>/dev/null || true

    echo "✓ Done."
}

trap cleanup EXIT INT TERM

echo "──────────────────────────────────────────────"
echo "Development environment is running."
echo
echo "Website:  http://localhost:8080"
echo "API:      http://127.0.0.1:5000"
echo
echo "Press Ctrl+C to stop everything."
echo "──────────────────────────────────────────────"

wait
