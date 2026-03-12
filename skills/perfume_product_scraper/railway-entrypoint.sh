#!/usr/bin/env bash
# Optional: use this as ENTRYPOINT in a fork of vignesh07/clawdbot-railway-template
# to copy default-skills (e.g. perfume_product_scraper) into /data/workspace/skills on first run.
#
# In the fork: COPY this file as /usr/local/bin/railway-entrypoint.sh, chmod +x,
# then in Dockerfile use:
#   ENTRYPOINT ["/usr/local/bin/railway-entrypoint.sh"]
#   CMD ["node", "src/server.js"]
#
# Ensure the image has default-skills at /app/default-skills (COPY skills /app/default-skills).

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
