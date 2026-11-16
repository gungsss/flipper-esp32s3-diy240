# Shared paths; source only from our own build/flash entrypoints.
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="${SOURCE_DIR:-$ROOT/.work/upstream}"
