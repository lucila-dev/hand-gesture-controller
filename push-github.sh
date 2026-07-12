#!/bin/bash
# Push to GitHub without writing to ~/.config (which may be root-owned).
set -euo pipefail
cd "$(dirname "$0")"

export XDG_CONFIG_HOME="$(pwd)/.gh-config"
mkdir -p "$XDG_CONFIG_HOME/gh"

git config http.postBuffer 524288000

if ! gh auth status -h github.com &>/dev/null; then
  echo "Log in to GitHub (browser will open)…"
  gh auth login -h github.com -p https -w
fi

echo "Creating repo and pushing…"
gh repo create hand-gesture-controller --public --source=. --remote=origin --push

echo "Done."
