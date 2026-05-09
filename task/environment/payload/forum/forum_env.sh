export FORUM_URL="${FORUM_URL:-http://localhost:8080}"
export FORUM_FIXTURE="${FORUM_FIXTURE:-default}"

if command -v forum-serverctl >/dev/null 2>&1; then
  forum-serverctl ensure "$FORUM_FIXTURE" >/dev/null 2>&1 || true
fi
