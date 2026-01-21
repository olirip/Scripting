#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <worktree-path>"
}

if [[ $# -ne 1 ]]; then
  usage
  exit 1
fi

target_path="$1"

if ! repo_root="$(git -C . rev-parse --show-toplevel 2>/dev/null)"; then
  echo "Error: not inside a git repository."
  exit 1
fi

git -C "$repo_root" worktree add "$target_path"

# Copy .env* and specific certificate files into the new worktree.
shopt -s nullglob
env_files=("$repo_root"/.env*)
cert_files=("$repo_root"/certificate.dev.crt "$repo_root"/certificate.dev.key)

for file in "${env_files[@]}" "${cert_files[@]}"; do
  if [[ -f "$file" ]]; then
    cp -p "$file" "$target_path/"
  fi
done
