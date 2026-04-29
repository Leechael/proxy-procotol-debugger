#!/usr/bin/env bash
set -euo pipefail

repo_dir="${1:-.}"
workflows_dir="$repo_dir/.github/workflows"
env_file="$repo_dir/release-naming.env"

if [[ ! -d "$workflows_dir" ]]; then
  echo "missing workflows dir: $workflows_dir" >&2
  exit 1
fi

if [[ ! -f "$env_file" ]]; then
  echo "missing release naming contract: $env_file" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$env_file"

for key in IMAGE_NAME TAG_PREFIX REGISTRY; do
  if [[ -z "${!key:-}" ]]; then
    echo "release-naming.env missing value: $key" >&2
    exit 1
  fi
done

echo "Auditing release naming in $repo_dir"

if ! rg -n --fixed-strings "${TAG_PREFIX}*" "$workflows_dir/release-on-tag.yml" >/dev/null; then
  echo "release-on-tag.yml trigger does not match TAG_PREFIX: ${TAG_PREFIX}*" >&2
  exit 1
fi

for f in "$workflows_dir/release-command.yml" "$workflows_dir/release-on-tag.yml" "$repo_dir/scripts/next-version.sh"; do
  if [[ ! -f "$f" ]]; then
    echo "missing required file: $f" >&2
    exit 1
  fi
  if ! rg -n "release-naming.env|TAG_PREFIX|IMAGE_NAME|REGISTRY" "$f" >/dev/null; then
    echo "file does not appear to use naming contract: $f" >&2
    exit 1
  fi
done

echo "release naming audit passed"
