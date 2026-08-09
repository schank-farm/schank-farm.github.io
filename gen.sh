#!/usr/bin/env bash
# gen.sh - Rebuild this Hugo Website

set -e

# Determine Project Root Directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$1" = "--new" ] || [ "$1" = "-n" ]; then
  TITLE="$2"
  if [ -z "$TITLE" ]; then
    echo "Error: Title required. Usage: ./gen.sh --new \"My Article Title\""
    exit 1
  fi

  SLUG=$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g')
  if [ -z "$SLUG" ]; then
    SLUG="article"
  fi

  echo "=================================================="
  echo "✨ Creating New Article Draft: $TITLE (slug: $SLUG)"
  echo "=================================================="
  hugo new "$SLUG/index.md"
  echo "=================================================="
  echo "✅ Article draft created in src/$SLUG/index.md"
  exit 0
fi

echo "=================================================="
echo "Schank Farms - Site Generator"
echo "=================================================="

# Rebuild Hugo static site into docs/
echo "Rebuilding Hugo static site into docs/..."
hugo build

echo "=================================================="
echo "✅ Build Complete! Generated site is ready in docs/"
echo "=================================================="
