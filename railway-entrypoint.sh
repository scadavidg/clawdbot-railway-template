#!/usr/bin/env bash
# Copies default-skills (e.g. perfume_product_scraper) into /data/workspace/skills on first run.
# Used with ENTRYPOINT in this fork; default-skills are at /app/default-skills.

set -euo pipefail
WORKSPACE="${OPENCLAW_WORKSPACE_DIR:-/data/workspace}"
DEFAULT_SKILLS="/app/default-skills"

if [[ -d "$DEFAULT_SKILLS" ]]; then
  SKILLS_DEST="$WORKSPACE/skills"
  mkdir -p "$SKILLS_DEST"
  for skill in "$DEFAULT_SKILLS"/*; do
    [[ -d "$skill" ]] || continue
    name=$(basename "$skill")
    if [[ ! -d "$SKILLS_DEST/$name" ]]; then
      cp -R "$skill" "$SKILLS_DEST/"
      echo "[entrypoint] Copied default skill: $name"
    fi
  done
fi

exec "$@"
