#!/bin/sh
# Usage:  sh apply_patch_mac_linux.sh "/path/to/your/game.3ds"      (or a folder with the extracted RomFS)
cd "$(dirname "$0")" || exit 1
if [ -z "$1" ]; then
  echo "Usage: sh apply_patch_mac_linux.sh \"/path/to/your/game.3ds\""
  exit 1
fi
if command -v python3 >/dev/null 2>&1; then
  exec python3 kb6_patcher.py "$@"
else
  echo "Python 3 was not found. Install it from https://www.python.org/downloads/ and try again."
  exit 1
fi
