#!/usr/bin/env bash
# gen.sh - Rebuild Peachy Keen Green Hugo Website

set -e

# Determine Project Root Directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "🌱 Peachy Keen Green - Site Generator"
echo "=================================================="

# Rebuild Hugo static site into docs/
echo "Rebuilding Hugo static site into docs/..."
hugo build

echo "=================================================="
echo "✅ Build Complete! Generated site is ready in docs/"
echo "=================================================="
